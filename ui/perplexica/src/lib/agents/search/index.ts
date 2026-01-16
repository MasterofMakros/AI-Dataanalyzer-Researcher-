import { ResearcherOutput, SearchAgentInput } from './types';
import SessionManager from '@/lib/session';
import { classify } from './classifier';
import Researcher from './researcher';
import { getWriterPrompt } from '@/lib/prompts/search/writer';
import { WidgetExecutor } from './widgets';
import db from '@/lib/db';
import { chats, messages } from '@/lib/db/schema';
import { and, eq, gt } from 'drizzle-orm';
import { Claim, ClaimBlock, ResearchBlock, TextBlock } from '@/lib/types';
import { getClaimsPrompt } from '@/lib/prompts/search/claims';
import { z } from 'zod';
import { randomUUID } from '@/lib/utils/crypto';

class SearchAgent {
  async searchAsync(session: SessionManager, input: SearchAgentInput) {
    const exists = await db.query.messages.findFirst({
      where: and(
        eq(messages.chatId, input.chatId),
        eq(messages.messageId, input.messageId),
      ),
    });

    if (!exists) {
      await db.insert(messages).values({
        chatId: input.chatId,
        messageId: input.messageId,
        backendId: session.id,
        query: input.followUp,
        createdAt: new Date().toISOString(),
        status: 'answering',
        responseBlocks: [],
      });
    } else {
      await db
        .delete(messages)
        .where(
          and(eq(messages.chatId, input.chatId), gt(messages.id, exists.id)),
        )
        .execute();
      await db
        .update(messages)
        .set({
          status: 'answering',
          backendId: session.id,
          responseBlocks: [],
        })
        .where(
          and(
            eq(messages.chatId, input.chatId),
            eq(messages.messageId, input.messageId),
          ),
        )
        .execute();
    }

    const classification = await classify({
      chatHistory: input.chatHistory,
      enabledSources: input.config.sources,
      query: input.followUp,
      llm: input.config.llm,
    });

    const widgetPromise = WidgetExecutor.executeAll({
      classification,
      chatHistory: input.chatHistory,
      followUp: input.followUp,
      llm: input.config.llm,
    }).then((widgetOutputs) => {
      widgetOutputs.forEach((o) => {
        session.emitBlock({
          id: randomUUID(),
          type: 'widget',
          data: {
            widgetType: o.type,
            params: o.data,
          },
        });
      });
      return widgetOutputs;
    });

    let searchPromise: Promise<ResearcherOutput> | null = null;

    if (!classification.classification.skipSearch) {
      const researcher = new Researcher();
      searchPromise = researcher.research(session, {
        chatHistory: input.chatHistory,
        followUp: input.followUp,
        classification: classification,
        config: input.config,
      });
    }

    const [widgetOutputs, searchResults] = await Promise.all([
      widgetPromise,
      searchPromise,
    ]);

    session.emit('data', {
      type: 'researchComplete',
    });

    const researchBlocks = session
      .getAllBlocks()
      .filter(
        (block): block is ResearchBlock => block.type === 'research',
      );
    const latestResearchBlock = researchBlocks[researchBlocks.length - 1];

    if (latestResearchBlock) {
      const hasSynthesisStep = latestResearchBlock.data.subSteps.some(
        (step) => step.type === 'synthesis',
      );

      if (!hasSynthesisStep) {
        latestResearchBlock.data.subSteps.push({
          id: randomUUID(),
          type: 'synthesis',
        });
      }

      latestResearchBlock.data.phase = 'synthesis';
      session.updateBlock(latestResearchBlock.id, [
        {
          op: 'replace',
          path: '/data/subSteps',
          value: latestResearchBlock.data.subSteps,
        },
        {
          op: 'replace',
          path: '/data/phase',
          value: latestResearchBlock.data.phase,
        },
      ]);
    }

    const finalContext =
      searchResults?.searchFindings
        .map(
          (f, index) =>
            `<result index=${index + 1} title=${f.metadata.title}>${f.content}</result>`,
        )
        .join('\n') || '';

    const widgetContext = widgetOutputs
      .map((o) => {
        return `<result>${o.llmContext}</result>`;
      })
      .join('\n-------------\n');

    const finalContextWithWidgets = `<search_results note="These are the search results and assistant can cite these">\n${finalContext}\n</search_results>\n<widgets_result noteForAssistant="Its output is already showed to the user, assistant can use this information to answer the query but do not CITE this as a souce">\n${widgetContext}\n</widgets_result>`;

    const writerPrompt = getWriterPrompt(
      finalContextWithWidgets,
      input.config.systemInstructions,
      input.config.mode,
    );
    const answerStream = input.config.llm.streamText({
      messages: [
        {
          role: 'system',
          content: writerPrompt,
        },
        ...input.chatHistory,
        {
          role: 'user',
          content: input.followUp,
        },
      ],
    });

    let responseBlockId = '';
    let finalAnswer = '';

    for await (const chunk of answerStream) {
      if (!responseBlockId) {
        const block: TextBlock = {
          id: randomUUID(),
          type: 'text',
          data: chunk.contentChunk,
        };

        session.emitBlock(block);

        responseBlockId = block.id;
        finalAnswer = block.data;
      } else {
        const block = session.getBlock(responseBlockId) as TextBlock | null;

        if (!block) {
          continue;
        }

        block.data += chunk.contentChunk;
        finalAnswer = block.data;

        session.updateBlock(block.id, [
          {
            op: 'replace',
            path: '/data',
            value: block.data,
          },
        ]);
      }
    }

    const sourcesForClaims = searchResults?.searchFindings ?? [];

    if (finalAnswer.trim()) {
      try {
        const claimsSchema = z.object({
          claims: z.array(
            z.object({
              text: z.string().min(1),
              evidenceIds: z.array(z.number().int().positive()),
              verified: z.boolean(),
            }),
          ),
        });

        const claimsResponse = await input.config.llm.generateObject<
          typeof claimsSchema
        >({
          schema: claimsSchema,
          messages: [
            {
              role: 'system',
              content: getClaimsPrompt(sourcesForClaims),
            },
            {
              role: 'user',
              content: `Answer:\n${finalAnswer}`,
            },
          ],
          options: {
            temperature: 0.1,
          },
        });

        const claims: Claim[] = claimsResponse.claims
          .map((claim) => {
            const uniqueEvidenceIds = Array.from(
              new Set(
                claim.evidenceIds.filter(
                  (id) => id > 0 && id <= sourcesForClaims.length,
                ),
              ),
            );

            return {
              id: randomUUID(),
              text: claim.text.trim(),
              evidenceIds: uniqueEvidenceIds,
              verified: claim.verified && uniqueEvidenceIds.length > 0,
            };
          })
          .filter((claim) => claim.text.length > 0);

        if (claims.length > 0) {
          const claimBlock: ClaimBlock = {
            id: randomUUID(),
            type: 'claim',
            data: claims,
          };
          session.emitBlock(claimBlock);
        }
      } catch (error) {
        console.warn('Failed to generate claims:', error);
      }
    }

    session.emit('end', {});

    await db
      .update(messages)
      .set({
        status: 'completed',
        responseBlocks: session.getAllBlocks(),
      })
      .where(
        and(
          eq(messages.chatId, input.chatId),
          eq(messages.messageId, input.messageId),
        ),
      )
      .execute();
  }
}

export default SearchAgent;
