import {
  ActionOutput,
  ResearcherInput,
  ResearcherOutput,
  SearchActionOutput,
} from '../types';
import { randomUUID } from '@/lib/utils/crypto';
import { ActionRegistry } from './actions';
import { getResearcherPrompt } from '@/lib/prompts/search/researcher';
import SessionManager from '@/lib/session';
import { Message, ReasoningResearchBlock } from '@/lib/types';
import { mergeEvidence, normalizeChunksEvidence } from '@/lib/utils/evidence';
import formatChatHistoryAsString from '@/lib/utils/formatHistory';
import { ToolCall } from '@/lib/models/types';

class Researcher {
  async research(
    session: SessionManager,
    input: ResearcherInput,
  ): Promise<ResearcherOutput> {
    let actionOutput: ActionOutput[] = [];
    let maxIteration =
      input.config.mode === 'speed'
        ? 2
        : input.config.mode === 'balanced'
          ? 6
          : 25;

    const availableTools = ActionRegistry.getAvailableActionTools({
      classification: input.classification,
      fileIds: input.config.fileIds,
      mode: input.config.mode,
      sources: input.config.sources,
    });

    const availableActionsDescription =
      ActionRegistry.getAvailableActionsDescriptions({
        classification: input.classification,
        fileIds: input.config.fileIds,
        mode: input.config.mode,
        sources: input.config.sources,
      });

    const researchBlockId = randomUUID();

    session.emitBlock({
      id: researchBlockId,
      type: 'research',
      data: {
        phase: 'analysis',
        subSteps: [],
      },
    });

    const agentMessageHistory: Message[] = [
      {
        role: 'user',
        content: `
          <conversation>
          ${formatChatHistoryAsString(input.chatHistory.slice(-10))}
           User: ${input.followUp} (Standalone question: ${input.classification.standaloneFollowUp})
           </conversation>
        `,
      },
    ];

    for (let i = 0; i < maxIteration; i++) {
      const researcherPrompt = getResearcherPrompt(
        availableActionsDescription,
        input.config.mode,
        i,
        maxIteration,
        input.config.fileIds,
      );

      const actionStream = input.config.llm.streamText({
        messages: [
          {
            role: 'system',
            content: researcherPrompt,
          },
          ...agentMessageHistory,
        ],
        tools: availableTools,
      });

      const block = session.getBlock(researchBlockId);

      let reasoningEmitted = false;
      let reasoningId = randomUUID();

      let finalToolCalls: ToolCall[] = [];

      for await (const partialRes of actionStream) {
        if (partialRes.toolCallChunk.length > 0) {
          partialRes.toolCallChunk.forEach((tc) => {
            if (
              tc.name === '__reasoning_preamble' &&
              tc.arguments['plan'] &&
              !reasoningEmitted &&
              block &&
              block.type === 'research'
            ) {
              reasoningEmitted = true;
              block.data.phase = 'analysis';

              block.data.subSteps.push({
                id: reasoningId,
                type: 'reasoning',
                reasoning: tc.arguments['plan'],
              });

              session.updateBlock(researchBlockId, [
                {
                  op: 'replace',
                  path: '/data/subSteps',
                  value: block.data.subSteps,
                },
                {
                  op: 'replace',
                  path: '/data/phase',
                  value: block.data.phase,
                },
              ]);
            } else if (
              tc.name === '__reasoning_preamble' &&
              tc.arguments['plan'] &&
              reasoningEmitted &&
              block &&
              block.type === 'research'
            ) {
              const subStepIndex = block.data.subSteps.findIndex(
                (step: any) => step.id === reasoningId,
              );

              if (subStepIndex !== -1) {
                const subStep = block.data.subSteps[
                  subStepIndex
                ] as ReasoningResearchBlock;
                subStep.reasoning = tc.arguments['plan'];
                block.data.phase = 'analysis';
                session.updateBlock(researchBlockId, [
                  {
                    op: 'replace',
                    path: '/data/subSteps',
                    value: block.data.subSteps,
                  },
                  {
                    op: 'replace',
                    path: '/data/phase',
                    value: block.data.phase,
                  },
                ]);
              }
            }

            const existingIndex = finalToolCalls.findIndex(
              (ftc) => ftc.id === tc.id,
            );

            if (existingIndex !== -1) {
              finalToolCalls[existingIndex].arguments = tc.arguments;
            } else {
              finalToolCalls.push(tc);
            }
          });
        }
      }

      if (finalToolCalls.length === 0) {
        break;
      }

      if (finalToolCalls[finalToolCalls.length - 1].name === 'done') {
        break;
      }

      agentMessageHistory.push({
        role: 'assistant',
        content: '',
        tool_calls: finalToolCalls,
      });

      const startTime = Date.now();
      const actionResults = await ActionRegistry.executeAll(finalToolCalls, {
        llm: input.config.llm,
        embedding: input.config.embedding,
        session: session,
        mode: input.config.mode,
        researchBlockId: researchBlockId,
        fileIds: input.config.fileIds,
      });
      const endTime = Date.now();
      const durationMs = endTime - startTime;

      // Update the searching block with latency
      // We need to find the specific searching block generated by executeAll (specifically webSearch)
      // Since executeAll might generate multiple blocks, this is tricky. 
      // However, usually 'searching' blocks are emitted inside the specific actions.
      // WE NEED TO FIX THIS: Actions emit blocks, but they don't know the duration.
      // BETTER APPROACH: We can update the LAST 'searching' block if it exists.

      const currentBlock = session.getBlock(researchBlockId);
      if (currentBlock && currentBlock.type === 'research') {
        // Find the last 'searching' or 'upload_searching' block to update
        // We iterate backwards to find the most recent one corresponding to this action
        const subSteps = currentBlock.data.subSteps;
        let targetIndex = -1;

        for (let i = subSteps.length - 1; i >= 0; i--) {
          if (subSteps[i].type === 'searching' || subSteps[i].type === 'upload_searching') {
            targetIndex = i;
            break;
          }
        }

        if (targetIndex !== -1) {
          const targetStep = subSteps[targetIndex];
          // Only update if it doesn't already have duration (to avoid overwriting if we have multiple nested calls, though unlikely here)
          if (!('durationMs' in targetStep)) { // Cast check not strictly needed if we assume types, but logically safe
            (targetStep as any).durationMs = durationMs; // forceful assignment if type definition is tricky in this context

            session.updateBlock(researchBlockId, [
              {
                op: 'replace',
                path: '/data/subSteps',
                value: subSteps,
              }
            ]);
          }
        }
      }

      actionOutput.push(...actionResults);

      actionResults.forEach((action, i) => {
        agentMessageHistory.push({
          role: 'tool',
          id: finalToolCalls[i].id,
          name: finalToolCalls[i].name,
          content: JSON.stringify(action),
        });
      });
    }

    const searchResults = actionOutput
      .filter((a): a is SearchActionOutput => a.type === 'search_results')
      .flatMap((a) => a.results);

    const seenUrls = new Map<string, number>();

    const filteredSearchResults = searchResults
      .map((result, index) => {
        if (result.metadata.url && !seenUrls.has(result.metadata.url)) {
          seenUrls.set(result.metadata.url, index);
          return result;
        } else if (result.metadata.url && seenUrls.has(result.metadata.url)) {
          const existingIndex = seenUrls.get(result.metadata.url)!;

          const existingResult = searchResults[existingIndex];

          existingResult.content += `\n\n${result.content}`;
          const existingEvidence = existingResult.evidence ?? [];
          const incomingEvidence = result.evidence ?? [];
          if (incomingEvidence.length > 0) {
            const mergedEvidence = [
              ...existingEvidence,
              ...incomingEvidence,
            ];
            existingResult.evidence = mergedEvidence.filter(
              (entry, entryIndex, arr) =>
                arr.findIndex(
                  (candidate) =>
                    JSON.stringify(candidate) === JSON.stringify(entry),
                ) === entryIndex,
            );
          }
          existingResult.evidence = mergeEvidence(
            existingResult.evidence,
            result.evidence,
          );

          return undefined;
        }

        return result;
      })
      .filter((r): r is NonNullable<typeof r> => r !== undefined);

    const normalizedSearchResults = normalizeChunksEvidence(
      filteredSearchResults,
    );

    const finalBlock = session.getBlock(researchBlockId);
    if (finalBlock && finalBlock.type === 'research') {
      finalBlock.data.phase = 'synthesis';
      session.updateBlock(researchBlockId, [
        {
          op: 'replace',
          path: '/data/phase',
          value: finalBlock.data.phase,
        },
      ]);
    }

    session.emitBlock({
      id: randomUUID(),
      type: 'source',
      data: normalizedSearchResults,
    });

    return {
      findings: actionOutput,
      searchFindings: normalizedSearchResults,
    };
  }
}

export default Researcher;
