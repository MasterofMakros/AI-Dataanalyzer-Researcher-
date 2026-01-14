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
import { useMemo, useState } from 'react';
import { ResearchBlock, ResearchBlockSubStep } from '@/lib/types';

const getStepIcon = (step: ResearchBlockSubStep) => {
  switch (step.type) {
    case 'reasoning':
      return <Brain className="h-4 w-4" />;
    case 'searching':
      return <Search className="h-4 w-4" />;
    case 'upload_searching':
      return <UploadCloud className="h-4 w-4" />;
    case 'search_results':
      return <FileText className="h-4 w-4" />;
    case 'reading':
      return <BookSearch className="h-4 w-4" />;
    case 'upload_search_results':
      return <BookSearch className="h-4 w-4" />;
    case 'synthesis':
      return <Sparkles className="h-4 w-4" />;
    default:
      return <Brain className="h-4 w-4" />;
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

  if (step.type === 'upload_searching') {
    return step.queries;
  }

  if (step.type === 'search_results' || step.type === 'reading') {
    return step.reading
      .slice(0, 4)
      .map((result) => result.metadata.title || result.metadata.url || 'Source');
  }

  if (step.type === 'upload_search_results') {
    return step.results
      .slice(0, 4)
      .map(
        (result) =>
          result.metadata?.title || result.metadata?.fileName || 'Document',
      );
  }

  return [];
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

  const steps = block.data.subSteps;
  const stepDetails = useMemo(
    () =>
      steps.map((step) => ({
        id: step.id,
        details: getStepDetails(step),
      })),
    [steps],
  );

  if (!steps.length) return null;

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
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-black/70 dark:text-white/70" />
        ) : (
          <ChevronDown className="w-4 h-4 text-black/70 dark:text-white/70" />
        )}
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
                          {detail}
                        </span>
                      ))}
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
