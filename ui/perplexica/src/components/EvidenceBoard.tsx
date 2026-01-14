'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  CheckCircle2,
  FileText,
  Filter,
  Globe,
  Image as ImageIcon,
  Mic,
  Video,
} from 'lucide-react';
import Markdown from 'markdown-to-jsx';
import { Chunk, Claim, LocalSource } from '@/lib/types';
import { cn } from '@/lib/utils';

type EvidenceItem = {
  id: string;
  title: string;
  snippet: string;
  sourceType: 'web' | 'document' | 'audio' | 'video' | 'image';
  url?: string;
  filePath?: string;
  domain?: string;
  tags?: string[];
  fileType?: string;
  evidenceId?: number;
  page?: number;
  totalPages?: number;
  timecodeStart?: string;
  timecodeEnd?: string;
  timestamp?: number;
  confidence?: number;
  thumbnailUrl?: string;
  bbox?: string;
};

type EvidenceBoardProps = {
  answer: string;
  sources: Chunk[];
  localSources: LocalSource[];
  claims: Claim[];
};

const typeIconMap: Record<EvidenceItem['sourceType'], React.ReactNode> = {
  web: <Globe className="h-4 w-4" />,
  document: <FileText className="h-4 w-4" />,
  audio: <Mic className="h-4 w-4" />,
  video: <Video className="h-4 w-4" />,
  image: <ImageIcon className="h-4 w-4" />,
};

const typeLabelMap: Record<EvidenceItem['sourceType'], string> = {
  web: 'Web',
  document: 'Dokument',
  audio: 'Audio',
  video: 'Video',
  image: 'Bild',
};

const stripInlineTags = (text: string) =>
  text
    .replace(/<citation[^>]*>(.*?)<\/citation>/g, '$1')
    .replace(/<think>[\s\S]*?<\/think>/g, '');

const getDomain = (url?: string) => {
  if (!url) return undefined;
  try {
    return new URL(url).hostname;
  } catch {
    return undefined;
  }
};

const formatTimestamp = (timestamp?: number) => {
  if (timestamp === undefined) return undefined;
  const totalSeconds = Math.max(0, Math.floor(timestamp));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`;
};

const EvidenceBoard = ({
  answer,
  sources,
  localSources,
  claims,
}: EvidenceBoardProps) => {
  const evidenceItems = useMemo<EvidenceItem[]>(() => {
    const webItems = sources.map((source, index) => {
      const metadata = source.metadata ?? {};
      const evidence = source.evidence ?? [];
      const primaryEvidence = evidence[0] ?? {};
      const rawSnippet = source.content?.trim() ?? '';
      const snippet =
        rawSnippet.length > 260 ? `${rawSnippet.slice(0, 257)}...` : rawSnippet;
      const title = metadata.title || metadata.url || `Quelle ${index + 1}`;
      const domain = getDomain(metadata.url);
      const tags = Array.isArray(metadata.tags)
        ? metadata.tags.map(String)
        : metadata.tags
          ? String(metadata.tags).split(',').map((tag: string) => tag.trim())
          : [];
      const bbox = primaryEvidence.bbox ?? metadata.bbox;
      const bboxValue = bbox && Array.isArray(bbox) ? bbox.join(', ') : bbox;

      const evidenceId = metadata.evidenceId ?? index + 1;

      return {
        id: `${metadata.url || 'web'}-${index}`,
        title,
        snippet,
        sourceType: 'web',
        evidenceId,
        url: metadata.url,
        domain,
        tags,
        page: primaryEvidence.page ?? metadata.page,
        timecodeStart: primaryEvidence.timecodeStart ?? metadata.timecodeStart,
        timecodeEnd: primaryEvidence.timecodeEnd ?? metadata.timecodeEnd,
        timestamp: primaryEvidence.timestamp ?? metadata.timestamp,
        bbox: bboxValue,
      } as EvidenceItem;
    });

    const localItems = localSources.map((source) => {
      const fileType = source.filename.includes('.')
        ? source.filename.split('.').pop()?.toLowerCase()
        : undefined;

      return {
        id: source.id,
        title: source.filename,
        snippet: source.textSnippet,
        sourceType: source.sourceType,
        evidenceId: source.evidenceId,
        filePath: source.filePath,
        fileType,
        page: source.pageNumber,
        totalPages: source.totalPages,
        timecodeStart: source.timecodeStart,
        timecodeEnd: source.timecodeEnd,
        confidence: source.confidence,
        thumbnailUrl: source.thumbnailUrl,
      };
    });

    return [...webItems, ...localItems];
  }, [localSources, sources]);

  const evidenceLookup = useMemo(() => {
    const entries = evidenceItems
      .filter((item) => item.evidenceId !== undefined)
      .map((item) => [item.evidenceId as number, item]);
    return new Map(entries);
  }, [evidenceItems]);

  const typeOptions = useMemo(
    () =>
      Array.from(new Set(evidenceItems.map((item) => item.sourceType))).sort(),
    [evidenceItems],
  );
  const tagOptions = useMemo(
    () =>
      Array.from(
        new Set(
          evidenceItems.flatMap((item) => item.tags ?? []).filter(Boolean),
        ),
      ).sort(),
    [evidenceItems],
  );
  const domainOptions = useMemo(
    () =>
      Array.from(
        new Set(
          evidenceItems
            .map((item) => item.domain)
            .filter((domain): domain is string => Boolean(domain)),
        ),
      ).sort(),
    [evidenceItems],
  );
  const fileTypeOptions = useMemo(
    () =>
      Array.from(
        new Set(
          evidenceItems
            .map((item) => item.fileType)
            .filter((fileType): fileType is string => Boolean(fileType)),
        ),
      ).sort(),
    [evidenceItems],
  );

  const [activeTypes, setActiveTypes] = useState<EvidenceItem['sourceType'][]>(
    [],
  );
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedDomains, setSelectedDomains] = useState<string[]>([]);
  const [selectedFileTypes, setSelectedFileTypes] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [requireTimecode, setRequireTimecode] = useState(false);
  const [requirePage, setRequirePage] = useState(false);

  useEffect(() => {
    setActiveTypes((prev) =>
      prev.length > 0
        ? prev.filter((type) => typeOptions.includes(type))
        : typeOptions,
    );
    setSelectedTags((prev) => prev.filter((tag) => tagOptions.includes(tag)));
    setSelectedDomains((prev) =>
      prev.filter((domain) => domainOptions.includes(domain)),
    );
    setSelectedFileTypes((prev) =>
      prev.filter((fileType) => fileTypeOptions.includes(fileType)),
    );
  }, [domainOptions, fileTypeOptions, tagOptions, typeOptions]);

  const filteredItems = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    return evidenceItems.filter((item) => {
      const matchesType =
        activeTypes.length === 0 || activeTypes.includes(item.sourceType);
      const matchesTags =
        selectedTags.length === 0 ||
        selectedTags.some((tag) => item.tags?.includes(tag));
      const matchesDomains =
        selectedDomains.length === 0 ||
        (item.domain && selectedDomains.includes(item.domain));
      const matchesFileTypes =
        selectedFileTypes.length === 0 ||
        (item.fileType && selectedFileTypes.includes(item.fileType));
      const matchesTimecode =
        !requireTimecode ||
        Boolean(item.timecodeStart || item.timestamp !== undefined);
      const matchesPage = !requirePage || Boolean(item.page);
      const matchesTerm =
        !term ||
        item.title.toLowerCase().includes(term) ||
        item.snippet.toLowerCase().includes(term) ||
        item.url?.toLowerCase().includes(term) ||
        item.filePath?.toLowerCase().includes(term);
      return (
        matchesType &&
        matchesTags &&
        matchesDomains &&
        matchesFileTypes &&
        matchesTimecode &&
        matchesPage &&
        matchesTerm
      );
    });
  }, [
    activeTypes,
    evidenceItems,
    searchTerm,
    selectedTags,
    selectedDomains,
    selectedFileTypes,
    requireTimecode,
    requirePage,
  ]);

  const displayAnswer = useMemo(() => stripInlineTags(answer), [answer]);

  if (evidenceItems.length === 0 && !answer.trim()) {
    return null;
  }

  return (
    <section className="rounded-xl border border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-light-200 dark:border-dark-200">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          <h3 className="text-sm font-semibold text-black dark:text-white">
            Evidence Board
          </h3>
        </div>
        <div className="flex items-center gap-1 text-xs text-black/60 dark:text-white/60">
          <Filter className="h-3.5 w-3.5" />
          {filteredItems.length}/{evidenceItems.length} Quellen
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr] p-4">
        <div className="space-y-4">
          <div className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-4">
            <h4 className="text-xs font-semibold uppercase text-black/50 dark:text-white/50 mb-2">
              Antwort & Kernaussagen
            </h4>
            {displayAnswer.trim() ? (
              <Markdown className="prose prose-sm dark:prose-invert max-w-none text-black dark:text-white">
                {displayAnswer}
              </Markdown>
            ) : (
              <p className="text-sm text-black/60 dark:text-white/60">
                Noch keine Antwort vorhanden.
              </p>
            )}
          </div>

          <div className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-4">
            <h4 className="text-xs font-semibold uppercase text-black/50 dark:text-white/50 mb-3">
              Trust-but-Verify
            </h4>
            <div className="space-y-3">
              {claims.length === 0 && (
                <p className="text-sm text-black/60 dark:text-white/60">
                  Keine markierbaren Aussagen vorhanden.
                </p>
              )}
              {claims.map((claim) => {
                const claimEvidence = claim.evidenceIds
                  .map((id) => evidenceLookup.get(id))
                  .filter(Boolean);

                return (
                <div
                  key={claim.id}
                  className="rounded-md border border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary p-3"
                >
                  <p className="text-sm text-black dark:text-white">
                    {claim.text}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-black/60 dark:text-white/60">
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5',
                        claim.verified && claimEvidence.length > 0
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                          : 'bg-amber-500/10 text-amber-600 dark:text-amber-300',
                      )}
                    >
                      {claim.verified && claimEvidence.length > 0
                        ? 'Verifiziert'
                        : 'Unverifiziert'}
                    </span>
                    {claimEvidence.length > 0 ? (
                      claimEvidence.map((evidence) => {
                        const anchor = evidence?.evidenceId
                          ? `#evidence-${evidence.evidenceId}`
                          : evidence?.url;
                        const label = evidence?.evidenceId
                          ? `E${evidence.evidenceId}`
                          : evidence?.title;
                        return (
                          <a
                            key={evidence?.id ?? label}
                            href={anchor}
                            className="rounded-full border border-blue-500/20 bg-light-100 dark:bg-dark-100 px-2 py-0.5 text-blue-600 dark:text-blue-300 hover:border-blue-500/40"
                          >
                            {label}
                          </a>
                        );
                      })
                    ) : (
                      <span className="text-xs text-black/50 dark:text-white/50">
                        Unverifiziert
                      </span>
                    )}
                  </div>
                </div>
              )})}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-black/60 dark:text-white/60" />
                <h4 className="text-xs font-semibold uppercase text-black/50 dark:text-white/50">
                  Filter
                </h4>
              </div>
              <input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Suche nach Titel, Snippet oder URL"
                className="w-full sm:w-64 rounded-md border border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary px-3 py-1.5 text-xs text-black dark:text-white placeholder:text-black/40 dark:placeholder:text-white/40"
              />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {typeOptions.map((type) => {
                const isActive = activeTypes.includes(type);
                return (
                  <button
                    key={type}
                    onClick={() =>
                      setActiveTypes((prev) =>
                        prev.includes(type)
                          ? prev.filter((item) => item !== type)
                          : [...prev, type],
                      )
                    }
                    className={cn(
                      'flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition',
                      isActive
                        ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                        : 'border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary text-black/60 dark:text-white/60',
                    )}
                  >
                    {typeIconMap[type]}
                    {typeLabelMap[type]}
                  </button>
                );
              })}
            </div>
            {(tagOptions.length > 0 ||
              domainOptions.length > 0 ||
              fileTypeOptions.length > 0) && (
              <div className="mt-4 space-y-3">
                {tagOptions.length > 0 && (
                  <div>
                    <p className="text-[11px] font-semibold uppercase text-black/40 dark:text-white/40">
                      Tags
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {tagOptions.map((tag) => {
                        const isActive = selectedTags.includes(tag);
                        return (
                          <button
                            key={tag}
                            onClick={() =>
                              setSelectedTags((prev) =>
                                prev.includes(tag)
                                  ? prev.filter((item) => item !== tag)
                                  : [...prev, tag],
                              )
                            }
                            className={cn(
                              'rounded-full border px-2.5 py-0.5 text-xs transition',
                              isActive
                                ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                                : 'border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary text-black/60 dark:text-white/60',
                            )}
                          >
                            {tag}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
                {domainOptions.length > 0 && (
                  <div>
                    <p className="text-[11px] font-semibold uppercase text-black/40 dark:text-white/40">
                      Quellen
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {domainOptions.map((domain) => {
                        const isActive = selectedDomains.includes(domain);
                        return (
                          <button
                            key={domain}
                            onClick={() =>
                              setSelectedDomains((prev) =>
                                prev.includes(domain)
                                  ? prev.filter((item) => item !== domain)
                                  : [...prev, domain],
                              )
                            }
                            className={cn(
                              'rounded-full border px-2.5 py-0.5 text-xs transition',
                              isActive
                                ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                                : 'border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary text-black/60 dark:text-white/60',
                            )}
                          >
                            {domain}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
                {fileTypeOptions.length > 0 && (
                  <div>
                    <p className="text-[11px] font-semibold uppercase text-black/40 dark:text-white/40">
                      Dateityp
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {fileTypeOptions.map((fileType) => {
                        const isActive = selectedFileTypes.includes(fileType);
                        return (
                          <button
                            key={fileType}
                            onClick={() =>
                              setSelectedFileTypes((prev) =>
                                prev.includes(fileType)
                                  ? prev.filter((item) => item !== fileType)
                                  : [...prev, fileType],
                              )
                            }
                            className={cn(
                              'rounded-full border px-2.5 py-0.5 text-xs transition',
                              isActive
                                ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                                : 'border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary text-black/60 dark:text-white/60',
                            )}
                          >
                            {fileType.toUpperCase()}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setRequireTimecode((prev) => !prev)}
                    className={cn(
                      'rounded-full border px-2.5 py-0.5 text-xs transition',
                      requireTimecode
                        ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                        : 'border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary text-black/60 dark:text-white/60',
                    )}
                  >
                    Mit Timecode
                  </button>
                  <button
                    onClick={() => setRequirePage((prev) => !prev)}
                    className={cn(
                      'rounded-full border px-2.5 py-0.5 text-xs transition',
                      requirePage
                        ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                        : 'border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary text-black/60 dark:text-white/60',
                    )}
                  >
                    Mit Seitenzahl
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-3">
            {filteredItems.length === 0 && (
              <div className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-4 text-sm text-black/60 dark:text-white/60">
                Keine Quellen für die aktuellen Filter gefunden.
              </div>
            )}
            {filteredItems.map((item) => (
              <article
                key={item.id}
                id={item.evidenceId ? `evidence-${item.evidenceId}` : undefined}
                className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-4 scroll-mt-24"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 rounded-md bg-light-200/70 dark:bg-dark-200/70 p-2 text-black/70 dark:text-white/70">
                      {typeIconMap[item.sourceType]}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-black dark:text-white">
                        {item.title}
                      </p>
                      <p className="text-xs text-black/60 dark:text-white/60">
                        {typeLabelMap[item.sourceType]}
                        {item.page && (
                          <>
                            {' '}
                            • Seite {item.page}
                            {item.totalPages ? `/${item.totalPages}` : ''}
                          </>
                        )}
                        {item.timecodeStart && (
                          <>
                            {' '}
                            • {item.timecodeStart}
                            {item.timecodeEnd ? `–${item.timecodeEnd}` : ''}
                          </>
                        )}
                        {!item.timecodeStart &&
                          item.timestamp !== undefined && (
                            <> • {formatTimestamp(item.timestamp)}</>
                          )}
                        {item.confidence !== undefined && (
                          <> • Confidence {Math.round(item.confidence * 100)}%</>
                        )}
                      </p>
                    </div>
                  </div>
                  {(item.url || item.filePath) && (
                    <a
                      href={item.url || item.filePath}
                      target="_blank"
                      className="text-xs text-blue-500 hover:text-blue-600"
                      rel="noreferrer"
                    >
                      Öffnen
                    </a>
                  )}
                </div>

                {item.thumbnailUrl && item.sourceType === 'image' && (
                  <img
                    src={item.thumbnailUrl}
                    alt={item.title}
                    className="mt-3 h-32 w-full rounded-md object-cover"
                  />
                )}

                {item.snippet && (
                  <p className="mt-3 text-xs text-black/70 dark:text-white/70">
                    {item.snippet}
                  </p>
                )}

                {item.bbox && (
                  <p className="mt-2 text-[11px] text-black/50 dark:text-white/50">
                    BBox: {item.bbox}
                  </p>
                )}
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default EvidenceBoard;
