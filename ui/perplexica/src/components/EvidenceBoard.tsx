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
import {
  AudioPreviewCard,
  ImagePreviewCard,
  PdfPreviewCard,
  SourcePreviewModal,
  VideoPreviewCard,
} from './SourcePreviews';
import PreviewCard from './SourcePreviews/PreviewCard';
import { formatTimestamp, SourcePreviewType } from './SourcePreviews/previewUtils';
import { SourcePreview } from './SourcePreviews/SourcePreviewModal';

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
  timestampStart?: number;
  timestampEnd?: number;
  confidence?: number;
  thumbnailUrl?: string;
  ocrText?: string;
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

const normalizeText = (text: string) =>
  stripInlineTags(text).replace(/\s+/g, ' ').trim();

const getDomain = (url?: string) => {
  if (!url) return undefined;
  try {
    return new URL(url).hostname;
  } catch {
    return undefined;
  }
};

const EvidenceBoard = ({
  answer,
  sources,
  localSources,
  claims,
}: EvidenceBoardProps) => {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [previewSource, setPreviewSource] = useState<SourcePreview | null>(
    null,
  );

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
      const timestampStart =
        primaryEvidence.timestampStart ??
        metadata.timestampStart ??
        metadata.timestamp;
      const timestampEnd =
        primaryEvidence.timestampEnd ?? metadata.timestampEnd;

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
        totalPages: primaryEvidence.totalPages ?? metadata.totalPages,
        timecodeStart: primaryEvidence.timecodeStart ?? metadata.timecodeStart,
        timecodeEnd: primaryEvidence.timecodeEnd ?? metadata.timecodeEnd,
        timestampStart:
          primaryEvidence.timestampStart ??
          metadata.timestampStart ??
          primaryEvidence.timestamp ??
          metadata.timestamp,
        timestampEnd: primaryEvidence.timestampEnd ?? metadata.timestampEnd,
        thumbnailUrl: metadata.thumbnailUrl,
        ocrText: metadata.ocrText,
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
        timestampStart: source.timestampStart,
        timestampEnd: source.timestampEnd,
        confidence: source.confidence,
        thumbnailUrl: source.thumbnailUrl,
        ocrText: source.ocrText,
        tags: source.tags,
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
        Boolean(item.timecodeStart || item.timestampStart !== undefined);
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

  const openPreview = (item: EvidenceItem) => {
    const previewType: SourcePreviewType =
      item.sourceType === 'document' ? 'pdf' : item.sourceType;
    const timecodeStart =
      item.timecodeStart ?? formatTimestamp(item.timestampStart);
    const timecodeEnd = item.timecodeEnd ?? formatTimestamp(item.timestampEnd);

    setPreviewSource({
      title: item.title,
      type: previewType,
      href: item.url || item.filePath,
      snippet: item.snippet,
      pageNumber: item.page,
      totalPages: item.totalPages,
      timecodeStart,
      timecodeEnd,
      timestampStart: item.timestampStart,
      timestampEnd: item.timestampEnd,
      thumbnailUrl: item.thumbnailUrl,
      ocrText: item.ocrText,
      sourceLabel: item.domain || item.fileType?.toUpperCase(),
    });
    setIsPreviewOpen(true);
  };

  const closePreview = () => {
    setIsPreviewOpen(false);
    setPreviewSource(null);
  };

  const renderPreviewCard = (item: EvidenceItem, index: number) => {
    const previewType: SourcePreviewType =
      item.sourceType === 'document' ? 'pdf' : item.sourceType;
    const timecodeStart =
      item.timecodeStart ?? formatTimestamp(item.timestampStart);
    const timecodeEnd = item.timecodeEnd ?? formatTimestamp(item.timestampEnd);
    const sourceLabel = item.domain || item.fileType?.toUpperCase();

    if (previewType === 'pdf') {
      return (
        <PdfPreviewCard
          key={item.id}
          title={item.title}
          href={item.url || item.filePath}
          snippet={item.snippet}
          pageNumber={item.page}
          totalPages={item.totalPages}
          sourceLabel={sourceLabel}
          index={index}
          onClick={() => openPreview(item)}
        />
      );
    }

    if (previewType === 'audio') {
      return (
        <AudioPreviewCard
          key={item.id}
          title={item.title}
          href={item.url || item.filePath}
          snippet={item.snippet}
          timecodeStart={timecodeStart}
          timecodeEnd={timecodeEnd}
          sourceLabel={sourceLabel}
          index={index}
          onClick={() => openPreview(item)}
        />
      );
    }

    if (previewType === 'video') {
      return (
        <VideoPreviewCard
          key={item.id}
          title={item.title}
          href={item.url || item.filePath}
          snippet={item.snippet}
          timecodeStart={timecodeStart}
          timecodeEnd={timecodeEnd}
          thumbnailUrl={item.thumbnailUrl}
          sourceLabel={sourceLabel}
          index={index}
          onClick={() => openPreview(item)}
        />
      );
    }

    if (previewType === 'image') {
      return (
        <ImagePreviewCard
          key={item.id}
          title={item.title}
          href={item.url || item.filePath}
          snippet={item.snippet}
          ocrText={item.ocrText}
          thumbnailUrl={item.thumbnailUrl}
          sourceLabel={sourceLabel}
          index={index}
          onClick={() => openPreview(item)}
        />
      );
    }

    return (
      <PreviewCard key={item.id} onClick={() => openPreview(item)}>
        <div className="flex items-center justify-between text-xs text-black/50 dark:text-white/50">
          <div className="flex items-center space-x-2">
            <div className="bg-sky-500/10 text-sky-500 p-1 rounded-md">
              <Globe size={12} />
            </div>
            <span className="uppercase tracking-wide">Web</span>
          </div>
          <span>#{index + 1}</span>
        </div>
        <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis">
          {item.title}
        </p>
        {item.snippet && (
          <p className="text-xs text-black/70 dark:text-white/70 line-clamp-2">
            {item.snippet}
          </p>
        )}
        {sourceLabel && (
          <div className="text-[11px] text-black/40 dark:text-white/40">
            {sourceLabel}
          </div>
        )}
      </PreviewCard>
    );
  };

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
                            key={evidence.id}
                            href={evidence.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-500 hover:text-blue-600"
                          >
                            {evidence.title ?? `Quelle ${evidence.index}`}
                          </a>
                        ) : (
                          <span key={evidence.id}>
                            {evidence.title ?? `Quelle ${evidence.index}`}
                          </span>
                        ),
                      )
                    ) : (
                      <span>Keine Quellen verknüpft</span>
                    )}
                  </div>
                </div>
              )})}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-4">
            <div className="flex flex-wrap items-center gap-2">
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
                      'flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs transition',
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

          <div className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold uppercase text-black/50 dark:text-white/50">
                Quellen
              </p>
              <input
                type="search"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Filtern..."
                className="rounded-md border border-black/10 dark:border-white/10 bg-transparent px-2 py-1 text-xs"
              />
            </div>
            {filteredItems.length === 0 && (
              <div className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-secondary dark:bg-dark-secondary p-4 text-sm text-black/60 dark:text-white/60">
                Keine Quellen für die aktuellen Filter gefunden.
              </div>
            )}
            <div className="grid grid-cols-2 gap-2">
              {filteredItems.map((item, index) =>
                renderPreviewCard(item, index),
              )}
            </div>
          </div>
        </div>
      </div>

      <SourcePreviewModal
        isOpen={isPreviewOpen}
        onClose={closePreview}
        source={previewSource}
      />
    </section>
  );
};

export default EvidenceBoard;
