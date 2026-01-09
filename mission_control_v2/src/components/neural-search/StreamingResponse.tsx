import { useState } from 'react';
import { type Source, type Citation } from '@/types/neural-search';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface StreamingResponseProps {
  answer: string;
  citations: Citation[];
  sources: Source[];
  isStreaming: boolean;
  timestamp?: Date;
  onSourceClick: (sourceId: string) => void;
  onCitationHover: (citationIndex: number | null) => void;
}

const sourceTypeIcons: Record<string, string> = {
  pdf: '📄',
  audio: '🎤',
  image: '🖼️',
  email: '📧',
  video: '🎬',
  text: '📝',
};

export function StreamingResponse({
  answer,
  citations,
  sources,
  isStreaming,
  timestamp,
  onSourceClick,
  onCitationHover,
}: StreamingResponseProps) {
  const [hoveredCitation, setHoveredCitation] = useState<number | null>(null);

  // Parse answer to render citations as superscript
  const renderAnswerWithCitations = () => {
    // Match citation patterns like ¹, ², ³ or [1], [2], [3]
    const parts = answer.split(/([¹²³⁴⁵⁶⁷⁸⁹]|\[\d+\])/g);

    return parts.map((part, i) => {
      // Check if this is a citation marker
      const superscriptMatch = part.match(/^[¹²³⁴⁵⁶⁷⁸⁹]$/);
      const bracketMatch = part.match(/^\[(\d+)\]$/);

      if (superscriptMatch || bracketMatch) {
        const citationNum = superscriptMatch
          ? '¹²³⁴⁵⁶⁷⁸⁹'.indexOf(part) + 1
          : parseInt(bracketMatch![1]);

        const citation = citations.find(c => c.index === citationNum);

        return (
          <button
            key={i}
            className={`inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold rounded
              ${hoveredCitation === citationNum
                ? 'bg-teal-500 text-white scale-125'
                : 'bg-teal-900/50 text-teal-400 hover:bg-teal-800'
              } transition-all duration-200 mx-0.5 align-super`}
            onMouseEnter={() => {
              setHoveredCitation(citationNum);
              onCitationHover(citationNum);
            }}
            onMouseLeave={() => {
              setHoveredCitation(null);
              onCitationHover(null);
            }}
            onClick={() => citation && onSourceClick(citation.sourceId)}
          >
            {citationNum}
          </button>
        );
      }

      // Render bold text
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
      return boldParts.map((bp, j) => {
        if (bp.startsWith('**') && bp.endsWith('**')) {
          return (
            <strong key={`${i}-${j}`} className="text-slate-100 font-semibold">
              {bp.slice(2, -2)}
            </strong>
          );
        }
        return <span key={`${i}-${j}`}>{bp}</span>;
      });
    });
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diff < 60) return `vor ${diff} Sekunden`;
    if (diff < 3600) return `vor ${Math.floor(diff / 60)} Minuten`;
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="space-y-4">
      {/* Response Card */}
      <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl overflow-hidden backdrop-blur-sm">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
              <BrainIcon className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-medium text-slate-300">NEURAL SEARCH</span>
          </div>
          {timestamp && (
            <span className="text-xs text-slate-500">{formatTimestamp(timestamp)}</span>
          )}
        </div>

        {/* Answer Content */}
        <div className="p-5">
          <div className="text-slate-300 leading-relaxed">
            {renderAnswerWithCitations()}
            {isStreaming && (
              <span className="inline-block w-2 h-5 ml-1 bg-teal-400 animate-pulse" />
            )}
          </div>
        </div>

        {/* Sources Footer */}
        {sources.length > 0 && (
          <div className="px-5 py-4 bg-slate-800/30 border-t border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <LinkIcon className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Quellen ({sources.length})
                </span>
              </div>
              <Button variant="ghost" size="sm" className="text-xs text-slate-500 h-6 px-2">
                Alle anzeigen
              </Button>
            </div>

            {/* Source Pills */}
            <div className="flex gap-2 overflow-x-auto pb-1">
              {sources.map((source, idx) => {
                const citationNum = idx + 1;
                const isHighlighted = hoveredCitation === citationNum;

                return (
                  <button
                    key={source.id}
                    onClick={() => onSourceClick(source.id)}
                    onMouseEnter={() => {
                      setHoveredCitation(citationNum);
                      onCitationHover(citationNum);
                    }}
                    onMouseLeave={() => {
                      setHoveredCitation(null);
                      onCitationHover(null);
                    }}
                    className={`flex-shrink-0 flex flex-col items-center gap-1 p-2 rounded-lg border transition-all duration-200 min-w-[60px]
                      ${isHighlighted
                        ? 'bg-teal-900/50 border-teal-500 scale-105'
                        : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                      }`}
                  >
                    <span className="text-xs text-slate-500">
                      <sup className={isHighlighted ? 'text-teal-400' : ''}>{citationNum}</sup>
                    </span>
                    <span className="text-lg">{sourceTypeIcons[source.type] || '📄'}</span>
                    <Badge
                      variant="outline"
                      className={`text-[9px] px-1 py-0 ${source.confidence >= 95
                          ? 'border-emerald-700 text-emerald-400'
                          : source.confidence >= 90
                            ? 'border-teal-700 text-teal-400'
                            : 'border-amber-700 text-amber-400'
                        }`}
                    >
                      {source.confidence}%
                    </Badge>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Icons
function BrainIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2a9 9 0 0 0-9 9c0 4.17 2.84 7.67 6.69 8.69L12 22l2.31-2.31C18.16 18.67 21 15.17 21 11a9 9 0 0 0-9-9zm0 16c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z" />
    </svg>
  );
}

function LinkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  );
}
