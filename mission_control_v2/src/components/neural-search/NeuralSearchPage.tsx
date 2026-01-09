import { useState, useEffect, useRef, useCallback } from 'react';
import {
  type SearchProgress as SearchProgressType,
  type SearchResponse,
  type Source,
  type FollowUpQuestion,
  type PipelineStatus,
} from '@/types/neural-search';
import { SearchProgress } from './SearchProgress';
import { StreamingResponse } from './StreamingResponse';
import { SourceCard } from './SourceCard';
import { FollowUpSuggestions } from './FollowUpSuggestions';
import { PipelineStatusHeader } from './PipelineStatusHeader';
import { SendIcon, LoadingIcon, BrainIcon } from './NeuralSearchIcons';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

export function NeuralSearchPage() {
  const DEFAULT_PIPELINE_STATUS: PipelineStatus = {
    gpuStatus: 'offline',
    gpuModel: 'Unknown',
    vramUsage: 0,
    workersActive: 0,
    workersTotal: 3,
    queueDepth: 0,
    indexedDocuments: 0,
    lastSync: new Date(),
  };

  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchProgress, setSearchProgress] = useState<SearchProgressType | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [followUps, setFollowUps] = useState<FollowUpQuestion[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [, setHoveredCitation] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [streamedAnswer, setStreamedAnswer] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus>(DEFAULT_PIPELINE_STATUS);
  const [error, setError] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Update time every second
  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch pipeline status periodically
  useEffect(() => {
    const fetchPipelineStatus = async () => {
      try {
        const res = await fetch('/api/pipeline/status');
        if (res.ok) {
          const data = await res.json();
          setPipelineStatus({
            ...data,
            lastSync: new Date(data.lastSync),
          });
        }
      } catch {
        // Silently fail - use default status
      }
    };

    fetchPipelineStatus();
    const interval = setInterval(fetchPipelineStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Focus search with /
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      // Cancel with Escape
      if (e.key === 'Escape') {
        if (isSearching) {
          abortControllerRef.current?.abort();
          setIsSearching(false);
          setSearchProgress(null);
        } else if (selectedSourceId) {
          setSelectedSourceId(null);
        }
      }
      // Source shortcuts 1-9
      if (/^[1-9]$/.test(e.key) && response && !selectedSourceId) {
        const idx = parseInt(e.key) - 1;
        if (sources[idx]) {
          setSelectedSourceId(sources[idx].id);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSearching, selectedSourceId, response, sources]);

  // Execute search with SSE streaming
  const executeSearch = useCallback(async (searchQuery: string) => {
    // Abort any existing search
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    setIsSearching(true);
    setResponse(null);
    setSources([]);
    setFollowUps([]);
    setStreamedAnswer('');
    setSelectedSourceId(null);
    setError(null);
    setSearchProgress({ step: 'analyzing', progress: 5 });

    try {
      const res = await fetch('/api/neural-search/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, limit: 8 }),
        signal: abortControllerRef.current.signal,
      });

      if (!res.ok) {
        throw new Error(`Search failed: ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';
      let currentAnswer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            continue;
          }

          if (line.startsWith('data:')) {
            const dataStr = line.substring(5).trim();
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);

              // Handle different event types
              if (data.step !== undefined) {
                // Progress event
                setSearchProgress(data);
                if (data.step === 'complete') {
                  setIsSearching(false);
                }
              } else if (Array.isArray(data) && data[0]?.filename) {
                // Sources event
                setSources(data);
              } else if (data.id && data.answer) {
                // Complete event
                setResponse({
                  ...data,
                  timestamp: new Date(data.timestamp || Date.now()),
                  sources: sources,
                });
                setStreamedAnswer(data.answer);
                setIsStreaming(false);
              } else if (Array.isArray(data) && data[0]?.question) {
                // Follow-ups event
                setFollowUps(data);
              } else if (typeof data === 'string' || data.token) {
                // Token event (streaming answer)
                setIsStreaming(true);
                const token = typeof data === 'string' ? data : data.token;
                currentAnswer += token;
                setStreamedAnswer(currentAnswer);
              }
            } catch {
              // Handle plain text tokens
              if (dataStr && !dataStr.startsWith('{') && !dataStr.startsWith('[')) {
                setIsStreaming(true);
                currentAnswer += dataStr;
                setStreamedAnswer(currentAnswer);
              }
            }
          }
        }
      }

      setIsSearching(false);
      setIsStreaming(false);
      setSearchProgress({ step: 'complete', progress: 100 });

    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Suche fehlgeschlagen';
      if (err instanceof Error && err.name === 'AbortError') {
        // Search was cancelled
        setIsSearching(false);
        setSearchProgress(null);
        return;
      }

      console.error('Search error:', err);
      setError(errorMessage);
      setIsSearching(false);
      setSearchProgress(null);

      // Fallback to non-streaming API
      try {
        const res = await fetch('/api/neural-search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: searchQuery, limit: 8 }),
        });

        if (res.ok) {
          const data = await res.json();
          setResponse({
            ...data,
            timestamp: new Date(data.timestamp || Date.now()),
          });
          setSources(data.sources || []);
          setStreamedAnswer(data.answer || '');
          setError(null);

          // Fetch follow-ups
          const followUpRes = await fetch('/api/neural-search/follow-ups', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: searchQuery }),
          });
          if (followUpRes.ok) {
            setFollowUps(await followUpRes.json());
          }
        }
      } catch (fallbackErr) {
        console.error('Fallback search also failed:', fallbackErr);
      }
    }
  }, [sources]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isSearching) {
      executeSearch(query);
    }
  };

  const handleFollowUp = (question: string) => {
    setQuery(question);
    executeSearch(question);
  };

  const selectedSource = selectedSourceId
    ? sources.find((s) => s.id === selectedSourceId)
    : null;

  return (
    <div className="flex flex-col h-full bg-[hsl(210,20%,6%)]">
      {/* Pipeline Status Header */}
      <PipelineStatusHeader status={pipelineStatus} currentTime={currentTime} />

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full max-w-5xl mx-auto px-4 py-6 flex flex-col">
          {/* Search Input */}
          <form onSubmit={handleSearch} className="mb-6">
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Was möchtest du wissen?"
                className="w-full px-5 py-4 pr-14 text-lg bg-slate-900/80 border border-slate-700/50 rounded-xl
                  text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500/50 focus:ring-2
                  focus:ring-teal-500/20 transition-all backdrop-blur-sm"
                disabled={isSearching}
              />
              <button
                type="submit"
                disabled={!query.trim() || isSearching}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-lg bg-teal-600
                  hover:bg-teal-500 disabled:bg-slate-700 disabled:cursor-not-allowed flex items-center
                  justify-center transition-colors"
              >
                {isSearching ? (
                  <LoadingIcon className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <SendIcon className="w-5 h-5 text-white" />
                )}
              </button>
            </div>
            <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-400">/</kbd>
                Suche fokussieren
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-400">1-9</kbd>
                Quelle öffnen
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-400">Esc</kbd>
                Abbrechen
              </span>
            </div>
          </form>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-rose-900/20 border border-rose-700/50 rounded-lg text-rose-400 text-sm">
              {error}
            </div>
          )}

          {/* Results Area */}
          <ScrollArea className="flex-1" ref={resultsRef}>
            <div className="space-y-6 pb-6">
              {/* Search Progress */}
              {isSearching && searchProgress && <SearchProgress progress={searchProgress} />}

              {/* Streaming Response */}
              {(streamedAnswer || response) && !isSearching && (
                <StreamingResponse
                  answer={streamedAnswer || response?.answer || ''}
                  citations={response?.citations || []}
                  sources={sources}
                  isStreaming={isStreaming}
                  timestamp={response?.timestamp}
                  onSourceClick={setSelectedSourceId}
                  onCitationHover={setHoveredCitation}
                />
              )}

              {/* Selected Source Card */}
              {selectedSource && (
                <SourceCard
                  source={selectedSource}
                  citationNumber={sources.findIndex((s) => s.id === selectedSourceId) + 1}
                  isExpanded
                  onClose={() => setSelectedSourceId(null)}
                />
              )}

              {/* Follow-Up Suggestions */}
              {response && !selectedSourceId && followUps.length > 0 && (
                <FollowUpSuggestions questions={followUps} onSelect={handleFollowUp} />
              )}

              {/* Empty State */}
              {!isSearching && !response && !streamedAnswer && !error && (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-teal-500/20 to-cyan-600/20 flex items-center justify-center mb-6">
                    <BrainIcon className="w-10 h-10 text-teal-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-slate-200 mb-2">Neural Search</h2>
                  <p className="text-slate-500 max-w-md mb-8">
                    Durchsuche deine Dokumente, E-Mails, Audiodateien und mehr mit
                    KI-gestützter Analyse und verknüpften Quellen.
                  </p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {['Was weiß ich über meinen Telekom-Vertrag?', 'Zeige mir meine letzten Rechnungen', 'Welche Support-Tickets sind offen?'].map(
                      (suggestion) => (
                        <Button
                          key={suggestion}
                          variant="outline"
                          size="sm"
                          className="text-xs border-slate-700 text-slate-400 hover:text-slate-200 hover:border-teal-600"
                          onClick={() => {
                            setQuery(suggestion);
                            executeSearch(suggestion);
                          }}
                        >
                          {suggestion}
                        </Button>
                      )
                    )}
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}

