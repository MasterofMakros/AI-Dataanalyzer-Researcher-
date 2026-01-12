import { useState } from 'react';
import { type Source, type TranscriptLine } from '@/types/neural-search';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface SourceCardProps {
  source: Source;
  citationNumber: number;
  isExpanded?: boolean;
  onClose?: () => void;
}

export function SourceCard({ source, citationNumber, onClose }: SourceCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 95) return 'border-emerald-600 text-emerald-400 bg-emerald-900/20';
    if (confidence >= 90) return 'border-teal-600 text-teal-400 bg-teal-900/20';
    if (confidence >= 85) return 'border-amber-600 text-amber-400 bg-amber-900/20';
    return 'border-rose-600 text-rose-400 bg-rose-900/20';
  };

  const getTypeIcon = () => {
    switch (source.type) {
      case 'pdf': return '📄';
      case 'audio': return '🎤';
      case 'image': return '🖼️';
      case 'email': return '📧';
      case 'video': return '🎬';
      default: return '📝';
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-700/50 rounded-xl overflow-hidden backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-slate-800">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">
              <sup>{citationNumber}</sup>
            </span>
            <span className="text-lg">{getTypeIcon()}</span>
            <span className="text-sm font-medium text-slate-200 truncate">{source.filename}</span>
          </div>
          <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
            {source.page && <span>Seite {source.page}</span>}
            {source.line && <span>• Zeile {source.line}</span>}
            {source.timestamp && <span>• Zeitmarke: {source.timestamp}</span>}
            <span>• via {source.extractedVia}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge className={`text-[10px] px-2 py-0.5 ${getConfidenceColor(source.confidence)}`}>
            {source.confidence}%
          </Badge>
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-500 hover:text-slate-300 transition-colors p-1"
            >
              <CloseIcon className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Content based on type */}
      <div className="p-4">
        {source.type === 'pdf' && <PDFPreview source={source} />}
        {source.type === 'audio' && (
          <AudioPreview
            source={source}
            isPlaying={isPlaying}
            onPlayPause={() => setIsPlaying(!isPlaying)}
          />
        )}
        {source.type === 'image' && <ImagePreview source={source} />}
        {source.type === 'email' && <EmailPreview source={source} />}
        {(source.type === 'text' || source.type === 'video') && <GenericPreview source={source} />}
      </div>

      {/* Actions Footer */}
      <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/30 border-t border-slate-800">
        <Button variant="ghost" size="sm" className="text-xs text-slate-400 h-7">
          <FileOpenIcon className="w-3.5 h-3.5 mr-1.5" />
          {source.type === 'pdf' ? 'PDF öffnen' : 'Original öffnen'}
        </Button>
        <Button variant="ghost" size="sm" className="text-xs text-slate-400 h-7">
          <CopyIcon className="w-3.5 h-3.5 mr-1.5" />
          Text kopieren
        </Button>
        <Button variant="ghost" size="sm" className="text-xs text-slate-400 h-7">
          <SearchIcon className="w-3.5 h-3.5 mr-1.5" />
          Ähnliche finden
        </Button>
        <Button variant="ghost" size="sm" className="text-xs text-teal-400 h-7 ml-auto">
          <CheckIcon className="w-3.5 h-3.5 mr-1.5" />
          Verifizieren
        </Button>
      </div>
    </div>
  );
}

// PDF Preview Component
function PDFPreview({ source }: { source: Source }) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
      {/* Simulated PDF page */}
      <div className="bg-white/5 rounded border border-slate-600 p-4 font-mono text-sm">
        <div className="space-y-2">
          {source.highlightedText ? (
            <div className="relative">
              <div className="absolute -left-2 top-0 bottom-0 w-1 bg-teal-500 rounded" />
              <p className="text-teal-300 pl-2">{source.highlightedText}</p>
            </div>
          ) : (
            <p className="text-slate-400">{source.excerpt}</p>
          )}
        </div>
      </div>
    </div>
  );
}

// Audio Preview Component
function AudioPreview({
  source,
  isPlaying,
  onPlayPause,
}: {
  source: Source;
  isPlaying: boolean;
  onPlayPause: () => void;
}) {
  return (
    <div className="space-y-4">
      {/* Waveform visualization */}
      <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
        <div className="flex items-center gap-1 h-12 justify-center">
          {Array.from({ length: 50 }).map((_, i) => (
            <div
              key={i}
              className={`w-1 rounded-full transition-all duration-150 ${isPlaying ? 'bg-teal-500' : 'bg-slate-600'
                }`}
              style={{
                height: `${20 + ((i * 7) % 70)}%`,
                animationDelay: `${i * 50}ms`,
              }}
            />
          ))}
        </div>

        {/* Timestamp marker */}
        {source.timestamp && (
          <div className="flex items-center justify-center mt-2">
            <div className="text-xs text-teal-400 bg-teal-900/30 px-2 py-0.5 rounded">
              ▲ [{source.timestamp}] - Relevante Stelle
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex items-center justify-center gap-4 mt-4">
          <button className="text-slate-400 hover:text-slate-200 transition-colors">
            <RewindIcon className="w-5 h-5" />
          </button>
          <button
            onClick={onPlayPause}
            className="w-10 h-10 rounded-full bg-teal-600 hover:bg-teal-500 flex items-center justify-center transition-colors"
          >
            {isPlaying ? (
              <PauseIcon className="w-5 h-5 text-white" />
            ) : (
              <PlayIcon className="w-5 h-5 text-white ml-0.5" />
            )}
          </button>
          <button className="text-slate-400 hover:text-slate-200 transition-colors">
            <ForwardIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center justify-between mt-3 text-xs text-slate-500">
          <span>{source.timestamp || '00:00'}</span>
          <span>{source.duration || '00:00'}</span>
        </div>
      </div>

      {/* Transcript with diarization */}
      {source.transcript && source.transcript.length > 0 && (
        <div>
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
            <TranscriptIcon className="w-3.5 h-3.5" />
            Transkript mit Sprecher-Diarization
          </div>
          <ScrollArea className="h-40 bg-slate-800/50 rounded-lg border border-slate-700/50">
            <div className="p-3 space-y-2">
              {source.transcript.map((line, i) => (
                <TranscriptLineComponent key={i} line={line} />
              ))}
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}

function TranscriptLineComponent({ line }: { line: TranscriptLine }) {
  return (
    <div
      className={`flex gap-2 text-xs ${line.isHighlighted ? 'bg-teal-900/30 -mx-2 px-2 py-1 rounded border-l-2 border-teal-500' : ''
        }`}
    >
      <span className="text-slate-500 font-mono w-12 flex-shrink-0">[{line.timestamp}]</span>
      <span className="text-slate-400 w-16 flex-shrink-0">👤 {line.speaker}:</span>
      <span className={line.isHighlighted ? 'text-teal-300' : 'text-slate-300'}>
        "{line.text}"
      </span>
    </div>
  );
}

// Image Preview Component
function ImagePreview({ source }: { source: Source }) {
  return (
    <div className="space-y-4">
      {/* Image with bounding box overlay */}
      <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50 relative">
        <div className="aspect-video bg-slate-700/50 rounded flex items-center justify-center relative overflow-hidden">
          {/* Placeholder for actual image */}
          <div className="text-4xl">🖼️</div>

          {/* Bounding box highlight */}
          {source.boundingBox && (
            <div
              className="absolute border-2 border-teal-400 bg-teal-400/10 rounded"
              style={{
                left: `${source.boundingBox.x}%`,
                top: `${source.boundingBox.y}%`,
                width: `${source.boundingBox.width}%`,
                height: `${source.boundingBox.height}%`,
              }}
            />
          )}
        </div>
      </div>

      {/* Extracted text */}
      <div>
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
          <TextIcon className="w-3.5 h-3.5" />
          Extrahierter Text (OCR via {source.extractedVia})
        </div>
        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
          <p className="text-sm text-slate-300">{source.excerpt}</p>
        </div>
      </div>
    </div>
  );
}

// Email Preview Component
function EmailPreview({ source }: { source: Source }) {
  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50">
      <div className="p-3 border-b border-slate-700/50 space-y-1">
        <div className="text-xs text-slate-500">
          <span className="text-slate-400">Von:</span> support@telekom.de
        </div>
        <div className="text-xs text-slate-500">
          <span className="text-slate-400">Betreff:</span> {source.filename}
        </div>
      </div>
      <div className="p-4">
        {source.highlightedText ? (
          <div className="relative">
            <div className="absolute -left-2 top-0 bottom-0 w-1 bg-teal-500 rounded" />
            <p className="text-sm text-teal-300 pl-2">{source.highlightedText}</p>
          </div>
        ) : (
          <p className="text-sm text-slate-300">{source.excerpt}</p>
        )}
      </div>
    </div>
  );
}

// Generic Preview Component
function GenericPreview({ source }: { source: Source }) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
      <p className="text-sm text-slate-300">{source.excerpt}</p>
    </div>
  );
}

// Icons
function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

function FileOpenIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
    </svg>
  );
}

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

function PlayIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}

function PauseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
    </svg>
  );
}

function RewindIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z" />
    </svg>
  );
}

function ForwardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z" />
    </svg>
  );
}

function TranscriptIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function TextIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h7" />
    </svg>
  );
}
