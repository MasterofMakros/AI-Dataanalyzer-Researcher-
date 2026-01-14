'use client';

import {
  Brain,
  Search,
  ChevronDown,
  ChevronUp,
  BookSearch,
  Sparkles,
  Check,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import { ResearchBlock, ResearchBlockSubStep, ResearchPhase } from '@/lib/types';
import { useChat } from '@/lib/hooks/useChat';
import FormatIcon from './LocalSources/FormatIcon';

type ResearchPhase = 'analysis' | 'search' | 'read' | 'synthesis';

const getPhaseForStep = (step: ResearchBlockSubStep): ResearchPhase => {
const ROADMAP_PHASE_LABELS: Record<ResearchPhase, string> = {
  analysis: 'Analyse',
  search: 'Suche',
  reading: 'Lesen',
  synthesis: 'Synthese',
};

const getStepPhase = (step: ResearchBlockSubStep): ResearchPhase => {
  if (step.type === 'reasoning') {
    return 'analysis';
  }

  if (step.type === 'searching' || step.type === 'upload_searching') {
    return 'search';
  }

  if (
    step.type === 'search_results' ||
    step.type === 'reading' ||
    step.type === 'upload_search_results'
  ) {
    return 'reading';
  }

  return 'analysis';
};

const getStepIcon = (step: ResearchBlockSubStep) => {
  if (step.type === 'reasoning') {
    return 'analysis';
  }

  if (step.type === 'searching' || step.type === 'upload_searching') {
    return 'search';
  }

  if (step.type === 'search_results') {
    return 'search';
  }

  return 'read';
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
      id: 'read',
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

    return 'pending';
  };

  const phaseSteps = phases.reduce(
    (acc, phase) => {
      acc[phase.id] = subSteps.filter(
        (step) => getPhaseForStep(step) === phase.id,
      );
      return acc;
    },
    {} as Record<ResearchPhase, ResearchBlockSubStep[]>,
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

  const readingSources = phaseSteps.read
    .filter(
      (step): step is Extract<ResearchBlockSubStep, { type: 'reading' }> =>
        step.type === 'reading',
    )
    .flatMap((step) => step.reading);

  const uploadResults = phaseSteps.read
    .filter(
      (
        step,
      ): step is Extract<
        ResearchBlockSubStep,
        { type: 'upload_search_results' }
      > => step.type === 'upload_search_results',
    )
    .flatMap((step) => step.results);
  const { researchEnded, loading } = useChat();
  const lastStep = block.data.subSteps[block.data.subSteps.length - 1];
  const currentPhase =
    block.data.phase || (lastStep ? getStepPhase(lastStep) : undefined);

  useEffect(() => {
    if (researchEnded && isLast) {
      setIsExpanded(false);
    } else if (status === 'answering' && isLast) {
      setIsExpanded(true);
    }
  }, [researchEnded, status]);

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
          <div>
            <p className="text-sm font-semibold text-black dark:text-white">
              Neural Search
            </p>
            <p className="text-xs text-black/60 dark:text-white/60">
              Prozess-Transparenz für die Antwort
            </p>
          </div>
          <Brain className="w-4 h-4 text-black dark:text-white" />
          <span className="text-sm font-medium text-black dark:text-white">
            Research Progress ({block.data.subSteps.length}{' '}
            {block.data.subSteps.length === 1 ? 'step' : 'steps'})
          </span>
          {currentPhase && (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-light-100 dark:bg-dark-100 text-black/60 dark:text-white/60 border border-light-200 dark:border-dark-200">
              {ROADMAP_PHASE_LABELS[currentPhase]}
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-black/70 dark:text-white/70" />
        ) : (
          <ChevronDown className="w-4 h-4 text-black/70 dark:text-white/70" />
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-light-200 dark:border-dark-200"
          >
            <div className="p-4 space-y-4">
              <div className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100/80 dark:bg-dark-100/60 px-3 py-2">
                <p className="text-[11px] uppercase tracking-[0.3em] text-black/50 dark:text-white/50">
                  Search Progress
                </p>
              </div>

              <div className="space-y-3">
                {phases.map((phase, index) => {
                  const phaseStatus = getPhaseStatus(phase.id);
                  const isActive = phaseStatus === 'active';
                  const isDone = phaseStatus === 'done';

                  return (
                    <div key={phase.id} className="flex gap-3">
                      <div className="flex flex-col items-center -mt-0.5">
                        <div
                          className={`rounded-full p-1.5 border transition ${
                            isDone
                              ? 'bg-emerald-500 border-emerald-500 text-white'
                              : isActive
                                ? 'bg-cyan-500/10 border-cyan-400 text-cyan-600 dark:text-cyan-200 animate-pulse'
                                : 'bg-light-100 dark:bg-dark-100 border-light-200 dark:border-dark-200 text-black/40 dark:text-white/40'
                          }`}
                        >
                          {isDone ? (
                            <Check className="w-4 h-4" />
                          ) : phase.id === 'analysis' ? (
                            <Brain className="w-4 h-4" />
                          ) : phase.id === 'search' ? (
                            <Search className="w-4 h-4" />
                          ) : phase.id === 'read' ? (
                            <BookSearch className="w-4 h-4" />
                          ) : (
                            <Sparkles className="w-4 h-4" />
                          )}
                        </div>
                        {index < phases.length - 1 && (
                          <div className="w-0.5 flex-1 min-h-[20px] bg-light-200 dark:bg-dark-200 mt-1.5" />
                        )}
                    <div className="flex-1 pb-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-medium text-black dark:text-white">
                          {getStepTitle(step, isStreaming)}
                        </span>
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-light-100 dark:bg-dark-100 text-black/60 dark:text-white/60 border border-light-200 dark:border-dark-200">
                          {ROADMAP_PHASE_LABELS[getStepPhase(step)]}
                        </span>
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
                          {phase.id !== 'synthesis' && (
                            <span className="text-xs text-black/50 dark:text-white/50">
                              {phase.id === 'analysis' &&
                                phaseSteps.analysis.length > 0 &&
                                `${phaseSteps.analysis.length} Step`}
                              {phase.id === 'search' &&
                                (searchQueries.length + uploadQueries.length > 0 ||
                                  searchResults.length > 0) &&
                                `${searchQueries.length + uploadQueries.length} Queries · ${searchResults.length} Ergebnisse`}
                              {phase.id === 'read' &&
                                (readingSources.length > 0 ||
                                  uploadResults.length > 0) &&
                                `${readingSources.length + uploadResults.length} Quellen`}
                            </span>
                          )}
                          {phase.id === 'synthesis' && (
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
                          </div>
                        )}

                        {phase.id === 'read' && readingSources.length > 0 && (
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
                          </div>
                        )}

                        {phase.id === 'read' && uploadResults.length > 0 && (
                          <div className="mt-3 grid gap-3 lg:grid-cols-3">
                            {uploadResults.slice(0, 4).map((result, idx) => {
                              const title =
                                (result.metadata &&
                                  (result.metadata.title ||
                                    result.metadata.fileName)) ||
                                'Untitled document';

                              const fileName =
                                result.metadata?.fileName ||
                                result.metadata?.title ||
                                '';
                              const ext = fileName.includes('.')
                                ? fileName.split('.').pop()?.toLowerCase() || ''
                                : '';

                              return (
                                <div
                                  key={idx}
                                  className="flex flex-row space-x-3 rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-2 cursor-pointer"
                                >
                                  <div className="mt-0.5 h-10 w-10 rounded-md bg-cyan-100 text-cyan-800 dark:bg-sky-500 dark:text-cyan-50 flex items-center justify-center">
                                    <FormatIcon format={ext} size={20} />
                                  </div>
                                  <div className="flex flex-col justify-center">
                                    <p className="text-[13px] text-black dark:text-white line-clamp-1">
                                      {title}
                                    </p>
                                    {ext && (
                                      <span className="text-[10px] text-black/50 dark:text-white/50 uppercase">
                                        {ext}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AssistantSteps;
