import { type FollowUpQuestion } from '@/types/neural-search';

interface FollowUpSuggestionsProps {
  questions: FollowUpQuestion[];
  onSelect: (question: string) => void;
}

export function FollowUpSuggestions({ questions, onSelect }: FollowUpSuggestionsProps) {
  if (questions.length === 0) return null;

  return (
    <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-5 backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
          <LightbulbIcon className="w-3.5 h-3.5 text-white" />
        </div>
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
          Verwandte Fragen
        </span>
      </div>

      {/* Question Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {questions.map((q) => (
          <button
            key={q.id}
            onClick={() => onSelect(q.question)}
            className="group flex items-start gap-3 p-3 rounded-lg border border-slate-700/50 bg-slate-800/30
              hover:border-teal-600/50 hover:bg-teal-900/20 transition-all duration-200 text-left"
          >
            <span className="text-lg flex-shrink-0 group-hover:scale-110 transition-transform">
              {q.icon}
            </span>
            <span className="text-sm text-slate-300 group-hover:text-teal-300 transition-colors leading-snug">
              {q.question}
            </span>
            <ArrowIcon className="w-4 h-4 text-slate-600 group-hover:text-teal-400 ml-auto flex-shrink-0 opacity-0 group-hover:opacity-100 transition-all" />
          </button>
        ))}
      </div>
    </div>
  );
}

// Icons
function LightbulbIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  );
}

function ArrowIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  );
}
