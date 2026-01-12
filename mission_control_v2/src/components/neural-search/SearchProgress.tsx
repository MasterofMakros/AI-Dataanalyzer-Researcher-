import { type SearchProgress as SearchProgressType, type SearchStep } from '@/types/neural-search';
import { Badge } from '@/components/ui/badge';

interface SearchProgressProps {
  progress: SearchProgressType;
}

const steps: { key: SearchStep; label: string; labelActive: string }[] = [
  { key: 'analyzing', label: 'Analysiere Anfrage', labelActive: 'Analysiere Anfrage...' },
  { key: 'searching', label: 'Durchsuche Dokumente', labelActive: 'Durchsuche Dokumente...' },
  { key: 'reading', label: 'Lese relevante Quellen', labelActive: 'Lese relevante Quellen...' },
  { key: 'synthesizing', label: 'Synthetisiere Antwort', labelActive: 'Synthetisiere Antwort...' },
];

const getStepIndex = (step: SearchStep): number => {
  const idx = steps.findIndex(s => s.key === step);
  return idx === -1 ? steps.length : idx;
};

export function SearchProgress({ progress }: SearchProgressProps) {
  const currentStepIndex = getStepIndex(progress.step);

  return (
    <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6 backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="relative">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center">
            <SearchIcon className="w-4 h-4 text-white" />
          </div>
          <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-amber-500 rounded-full animate-pulse" />
        </div>
        <span className="text-sm font-medium text-slate-300 uppercase tracking-wider">Searching</span>
      </div>

      {/* Progress Bar */}
      <div className="h-1 bg-slate-800 rounded-full mb-6 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-teal-500 to-cyan-400 transition-all duration-500 ease-out"
          style={{ width: `${progress.progress}%` }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step, index) => {
          const isComplete = index < currentStepIndex || progress.step === 'complete';
          const isActive = index === currentStepIndex && progress.step !== 'complete';
          const isPending = index > currentStepIndex;

          return (
            <div
              key={step.key}
              className={`flex items-center gap-3 transition-all duration-300 ${isPending ? 'opacity-40' : ''
                }`}
            >
              {/* Status Icon */}
              <div className="w-5 h-5 flex items-center justify-center">
                {isComplete && (
                  <div className="w-5 h-5 rounded-full bg-teal-500/20 flex items-center justify-center">
                    <CheckIcon className="w-3 h-3 text-teal-400" />
                  </div>
                )}
                {isActive && (
                  <div className="w-5 h-5 rounded-full border-2 border-teal-500 border-t-transparent animate-spin" />
                )}
                {isPending && (
                  <div className="w-2 h-2 rounded-full bg-slate-600" />
                )}
              </div>

              {/* Label */}
              <span className={`text-sm ${isActive ? 'text-teal-400 font-medium' :
                  isComplete ? 'text-slate-400' : 'text-slate-500'
                }`}>
                {isActive ? step.labelActive : step.label}
              </span>

              {/* Progress indicator for searching step */}
              {step.key === 'searching' && isActive && progress.documentsFound !== undefined && (
                <Badge variant="outline" className="ml-auto text-[10px] border-teal-700 text-teal-400">
                  {progress.documentsFound} / {progress.documentsTotal}
                </Badge>
              )}

              {/* Progress indicator for reading step */}
              {step.key === 'reading' && isActive && progress.sourcesRead !== undefined && (
                <Badge variant="outline" className="ml-auto text-[10px] border-teal-700 text-teal-400">
                  {progress.sourcesRead} / {progress.sourcesTotal}
                </Badge>
              )}

              {/* Completed indicator */}
              {isComplete && (
                <span className="ml-auto text-[10px] text-slate-500">[done]</span>
              )}
            </div>
          );
        })}
      </div>

      {/* Keywords & Stats */}
      {progress.keywords && progress.keywords.length > 0 && (
        <div className="mt-5 pt-4 border-t border-slate-800">
          <div className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Keywords</div>
            <div className="flex flex-wrap gap-1.5">
              {progress.keywords.map((keyword, i) => (
                <Badge key={i} variant="outline" className="text-xs border-slate-600 text-slate-400">
                  {keyword}
                </Badge>
              ))}
            </div>
            {progress.documentsFound !== undefined && (
              <div className="mt-3 text-xs text-slate-400">
                Gefunden: <span className="text-teal-400 font-medium">{progress.documentsFound}</span> relevante Dokumente
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reading Sources List */}
      {progress.step === 'reading' && progress.currentSource && (
        <div className="mt-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="animate-pulse">Lese:</span>
            <span className="text-slate-400 font-mono truncate">{progress.currentSource}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// Icons
function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}
