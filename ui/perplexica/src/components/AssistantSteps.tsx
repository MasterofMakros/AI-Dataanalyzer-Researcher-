'use client';

import {
  Brain,
  BookSearch,
  ChevronDown,
  ChevronUp,
  FileText,
  Search,
  Sparkles,
  UploadCloud,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import { ResearchBlock, ResearchBlockSubStep, ResearchPhase } from '@/lib/types';
import { useChat } from '@/lib/hooks/useChat';
import UploadSearchResultsPanel from './UploadSearchResultsPanel';

const ROADMAP_PHASE_LABELS: Record<ResearchPhase, string> = {
  analysis: 'Analyse',
  search: 'Suche',
  reading: 'Lesen',
  synthesis: 'Synthese',
};

const getPhaseForStep = (step: ResearchBlockSubStep): ResearchPhase => {
  if (step.type === 'reasoning') {
    return 'analysis';
  }
};

const getStepTitle = (step: ResearchBlockSubStep) => {
  switch (step.type) {
    case 'reasoning':
      return 'Thinking';
    case 'searching':
      return `Searching ${step.searching.length} ${
        step.searching.length === 1 ? 'query' : 'queries'
      }`;
    case 'search_results':
      return `Found ${step.reading.length} ${
        step.reading.length === 1 ? 'result' : 'results'
      }`;
    case 'reading':
      return `Reading ${step.reading.length} ${
        step.reading.length === 1 ? 'source' : 'sources'
      }`;
    case 'upload_searching':
      return 'Searching uploaded documents';
    case 'upload_search_results':
      return `Reading ${step.results.length} ${
        step.results.length === 1 ? 'document' : 'documents'
      }`;
    case 'synthesis':
      return 'Synthesizing answer';
    default:
      return 'Working';
  }
};

const getStepDetails = (step: ResearchBlockSubStep) => {
  if (step.type === 'reasoning') {
    return step.reasoning ? [step.reasoning] : [];
  }

  if (step.type === 'searching') {
    return step.searching;
  }

  return 'analysis';
};

const AssistantSteps = ({
  block,
  status,
  isLast,
}: {
  block: ResearchBlock;
  status: 'answering' | 'completed' | 'error';
  isLast: boolean;
}) => {
  const [isExpanded, setIsExpanded] = useState(
    isLast && status === 'answering' ? true : false,
  );
  const { researchEnded } = useChat();

  const phases: {
    id: ResearchPhase;
    label: string;
    description: string;
  }[] = [
    {
      id: 'analysis',
      label: 'Analyse',
      description: 'Analysiere Anfrage',
    },
    {
      id: 'search',
      label: 'Suche',
      description: 'Durchsuche Quellen',
    },
    {
      id: 'reading',
      label: 'Lesen',
      description: 'Lese relevante Quellen',
    },
    {
      id: 'synthesis',
      label: 'Synthese',
      description: 'Synthetisiere Antwort',
    },
  ];

  const subSteps = block.data.subSteps;
  const lastStep = subSteps[subSteps.length - 1];
  const lastPhase = lastStep ? getPhaseForStep(lastStep) : 'analysis';
  const synthesisComplete = researchEnded || status === 'completed';
  const activePhase = synthesisComplete ? 'synthesis' : lastPhase;
  const activePhaseIndex = phases.findIndex((phase) => phase.id === activePhase);

  const getPhaseStatus = (phaseId: ResearchPhase) => {
    const phaseIndex = phases.findIndex((phase) => phase.id === phaseId);

    if (synthesisComplete) {
      return 'done';
    }

    if (phaseIndex < activePhaseIndex) {
      return 'done';
    }

    if (phaseIndex === activePhaseIndex) {
      return 'active';
    }

  const steps = block.data.subSteps;
  const stepDetails = useMemo(
    () =>
      steps.map((step) => ({
        id: step.id,
        details: getStepDetails(step),
      })),
    [steps],
  );

  const searchQueries = phaseSteps.search
    .filter(
      (step): step is Extract<ResearchBlockSubStep, { type: 'searching' }> =>
        step.type === 'searching',
    )
    .flatMap((step) => step.searching);

  const uploadQueries = phaseSteps.search
    .filter(
      (
        step,
      ): step is Extract<ResearchBlockSubStep, { type: 'upload_searching' }> =>
        step.type === 'upload_searching',
    )
    .flatMap((step) => step.queries);

  const searchResults = phaseSteps.search
    .filter(
      (
        step,
      ): step is Extract<ResearchBlockSubStep, { type: 'search_results' }> =>
        step.type === 'search_results',
    )
    .flatMap((step) => step.reading);

  const readingSources = phaseSteps.reading
    .filter(
      (step): step is Extract<ResearchBlockSubStep, { type: 'reading' }> =>
        step.type === 'reading',
    )
    .flatMap((step) => step.reading);

  const uploadResults = phaseSteps.reading
    .filter(
      (
        step,
      ): step is Extract<
        ResearchBlockSubStep,
        { type: 'upload_search_results' }
      > => step.type === 'upload_search_results',
    )
    .flatMap((step) => step.results);

  const lastStepForPhase = block.data.subSteps[block.data.subSteps.length - 1];
  const currentPhase =
    block.data.phase || (lastStepForPhase ? getPhaseForStep(lastStepForPhase) : undefined);
  const maxPreviewItems = 4;

  useEffect(() => {
    if (researchEnded && isLast) {
      setIsExpanded(false);
    } else if (status === 'answering' && isLast) {
      setIsExpanded(true);
    }
  }, [researchEnded, status, isLast]);

  if (!block || block.data.subSteps.length === 0) return null;

  return (
    <div className="rounded-lg bg-light-secondary/80 dark:bg-dark-secondary/80 border border-light-200 dark:border-dark-200 overflow-hidden shadow-sm">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-light-200/70 dark:hover:bg-dark-200/70 transition duration-200"
      >
        <div className="flex items-center gap-2">
          <div className="rounded-full p-1.5 bg-cyan-100 text-cyan-800 dark:bg-cyan-500/20 dark:text-cyan-200">
            <Brain className="w-4 h-4" />
          </div>
          <div className="text-left">
            <p className="text-sm font-semibold text-black dark:text-white">
              Neural Search
            </p>
            <p className="text-xs text-black/60 dark:text-white/60">
              Research Progress ({steps.length}{' '}
              {steps.length === 1 ? 'step' : 'steps'})
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-black dark:text-white">
            Research Progress ({block.data.subSteps.length}{' '}
            {block.data.subSteps.length === 1 ? 'step' : 'steps'})
          </span>
          {currentPhase && (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-light-100 dark:bg-dark-100 text-black/60 dark:text-white/60 border border-light-200 dark:border-dark-200">
              {ROADMAP_PHASE_LABELS[currentPhase]}
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-black/70 dark:text-white/70" />
          ) : (
            <ChevronDown className="w-4 h-4 text-black/70 dark:text-white/70" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-light-200 dark:border-dark-200">
          <div className="p-4 space-y-3">
            {steps.map((step, index) => {
              const details = stepDetails.find((item) => item.id === step.id);
              return (
                <div
                  key={step.id}
                  className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-3"
                >
                  <div className="flex items-center gap-2 text-sm text-black dark:text-white">
                    <span className="rounded-md bg-light-200/70 dark:bg-dark-200/70 p-1.5">
                      {getStepIcon(step)}
                    </span>
                    <span className="font-medium">{getStepTitle(step)}</span>
                    <span className="text-xs text-black/50 dark:text-white/50">
                      #{index + 1}
                    </span>
                  </div>
                  {details && details.details.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {details.details.map((detail, detailIndex) => (
                        <span
                          key={`${step.id}-${detailIndex}`}
                          className="inline-flex items-center rounded-full border border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary px-2.5 py-0.5 text-[11px] text-black/70 dark:text-white/70"
                        >
                          {isDone ? (
                            <Check className="w-4 h-4" />
                          ) : phase.id === 'analysis' ? (
                            <Brain className="w-4 h-4" />
                          ) : phase.id === 'search' ? (
                            <Search className="w-4 h-4" />
                          ) : phase.id === 'reading' ? (
                            <BookSearch className="w-4 h-4" />
                          ) : (
                            <Sparkles className="w-4 h-4" />
                          )}
                        </div>
                        {index < phases.length - 1 && (
                          <div className="w-0.5 flex-1 min-h-[20px] bg-light-200 dark:bg-dark-200 mt-1.5" />
                        )}
                      </div>
                      <div className="flex-1 pb-1">
                        <div className="flex flex-wrap items-baseline justify-between gap-2">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-black dark:text-white">
                              {phase.label}
                            </p>
                            <p className="text-xs text-black/60 dark:text-white/60">
                              {phase.description}
                            </p>
                          </div>
                          {phase.id !== 'synthesis' ? (
                            <span className="text-xs text-black/50 dark:text-white/50">
                              {phase.id === 'analysis' &&
                                phaseSteps.analysis.length > 0 &&
                                `${phaseSteps.analysis.length} Step`}
                              {phase.id === 'search' &&
                                (searchQueries.length + uploadQueries.length > 0 ||
                                  searchResults.length > 0) &&
                                `${searchQueries.length + uploadQueries.length} Queries · ${searchResults.length} Ergebnisse`}
                              {phase.id === 'reading' &&
                                (readingSources.length > 0 ||
                                  uploadResults.length > 0) &&
                                `${readingSources.length + uploadResults.length} Quellen`}
                            </span>
                          ) : (
                            <span className="text-xs text-black/50 dark:text-white/50">
                              {synthesisComplete
                                ? 'Antwort bereit'
                                : 'Formuliere Antwort'}
                            </span>
                          )}
                        </div>

                        {phase.id === 'analysis' &&
                          phaseSteps.analysis.length > 0 && (
                            <div className="mt-2 space-y-1">
                              {phaseSteps.analysis.map((step) =>
                                step.type === 'reasoning' && step.reasoning ? (
                                  <p
                                    key={step.id}
                                    className="text-xs text-black/70 dark:text-white/70"
                                  >
                                    {step.reasoning}
                                  </p>
                                ) : null,
                              )}
                            </div>
                          )}

                        {phase.id === 'search' &&
                          (searchQueries.length > 0 ||
                            uploadQueries.length > 0) && (
                            <div className="flex flex-wrap gap-1.5 mt-2">
                              {[...searchQueries, ...uploadQueries].map(
                                (query, idx) => (
                                  <span
                                    key={`${query}-${idx}`}
                                    className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-light-100 dark:bg-dark-100 text-black/70 dark:text-white/70 border border-light-200 dark:border-dark-200"
                                  >
                                    {query}
                                  </span>
                                ),
                              )}
                            </div>
                          )}

                        {phase.id === 'search' && searchResults.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {searchResults.slice(0, 4).map((result, idx) => {
                              const url = result.metadata.url || '';
                              const title = result.metadata.title || 'Untitled';
                              const domain = url ? new URL(url).hostname : '';
                              const faviconUrl = domain
                                ? `https://s2.googleusercontent.com/s2/favicons?domain=${domain}&sz=128`
                                : '';

                              return (
                                <a
                                  key={idx}
                                  href={url}
                                  target="_blank"
                                  className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium bg-light-100 dark:bg-dark-100 text-black/70 dark:text-white/70 border border-light-200 dark:border-dark-200"
                                >
                                  {faviconUrl && (
                                    <img
                                      src={faviconUrl}
                                      alt=""
                                      className="w-3 h-3 rounded-sm flex-shrink-0"
                                      onError={(e) => {
                                        e.currentTarget.style.display = 'none';
                                      }}
                                    />
                                  )}
                                  <span className="line-clamp-1">{title}</span>
                                </a>
                              );
                            })}
                            {searchResults.length > maxPreviewItems && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-light-100 dark:bg-dark-100 text-black/60 dark:text-white/60 border border-light-200 dark:border-dark-200">
                                +{searchResults.length - maxPreviewItems} more
                              </span>
                            )}
                          </div>
                        )}

                        {phase.id === 'reading' && readingSources.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {readingSources.slice(0, 4).map((result, idx) => {
                              const url = result.metadata.url || '';
                              const title = result.metadata.title || 'Untitled';
                              const domain = url ? new URL(url).hostname : '';
                              const faviconUrl = domain
                                ? `https://s2.googleusercontent.com/s2/favicons?domain=${domain}&sz=128`
                                : '';

                              return (
                                <a
                                  key={idx}
                                  href={url}
                                  target="_blank"
                                  className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium bg-light-100 dark:bg-dark-100 text-black/70 dark:text-white/70 border border-light-200 dark:border-dark-200"
                                >
                                  {faviconUrl && (
                                    <img
                                      src={faviconUrl}
                                      alt=""
                                      className="w-3 h-3 rounded-sm flex-shrink-0"
                                      onError={(e) => {
                                        e.currentTarget.style.display = 'none';
                                      }}
                                    />
                                  )}
                                  <span className="line-clamp-1">{title}</span>
                                </a>
                              );
                            })}
                            {readingSources.length > maxPreviewItems && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-light-100 dark:bg-dark-100 text-black/60 dark:text-white/60 border border-light-200 dark:border-dark-200">
                                +{readingSources.length - maxPreviewItems} more
                              </span>
                            )}
                          </div>
                        )}

                        {phase.id === 'reading' && uploadResults.length > 0 && (
                          <div className="mt-2">
                            <UploadSearchResultsPanel results={uploadResults} />
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default AssistantSteps;
