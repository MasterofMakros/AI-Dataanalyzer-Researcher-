'use client';

import { useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Calendar, Filter, Folder, Tag } from 'lucide-react';
import { Chunk } from '@/lib/types';
import { cn } from '@/lib/utils';
import FormatIcon from './LocalSources/FormatIcon';

type UploadResult = Chunk & {
  metadata?: {
    fileName?: string;
    title?: string;
    fileExtension?: string;
    uploadedAt?: string;
    folder?: string;
    tags?: string[];
  };
};

const DATE_PRESETS = [
  { id: 'today', label: 'Heute', days: 1 },
  { id: 'last7', label: 'Letzte 7 Tage', days: 7 },
  { id: 'last30', label: 'Letzte 30 Tage', days: 30 },
  { id: 'older', label: 'Älter', days: 36500 },
];

const parseParam = (value: string | null) =>
  value ? value.split(',').map((item) => item.trim()).filter(Boolean) : [];

const toggleValue = (list: string[], value: string) =>
  list.includes(value) ? list.filter((item) => item !== value) : [...list, value];

const formatDate = (date?: string) => {
  if (!date) return 'Unbekannt';
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return 'Unbekannt';
  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(parsed);
};

const isInDateRange = (date: Date, rangeId: string) => {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = diff / (1000 * 60 * 60 * 24);

  if (rangeId === 'today') {
    return days <= 1;
  }

  if (rangeId === 'older') {
    return days > 30;
  }

  const preset = DATE_PRESETS.find((item) => item.id === rangeId);
  return preset ? days <= preset.days : false;
};

const UploadSearchResultsPanel = ({ results }: { results: UploadResult[] }) => {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedDates, setSelectedDates] = useState<string[]>([]);
  const [selectedFolders, setSelectedFolders] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  useEffect(() => {
    setSelectedTypes(parseParam(searchParams.get('uploadTypes')));
    setSelectedDates(parseParam(searchParams.get('uploadDates')));
    setSelectedFolders(parseParam(searchParams.get('uploadFolders')));
    setSelectedTags(parseParam(searchParams.get('uploadTags')));
  }, [searchParams]);

  const updateParam = (key: string, values: string[]) => {
    const params = new URLSearchParams(searchParams.toString());
    if (values.length > 0) {
      params.set(key, values.join(','));
    } else {
      params.delete(key);
    }
    const queryString = params.toString();
    router.replace(queryString ? `${pathname}?${queryString}` : pathname, {
      scroll: false,
    });
  };

  const normalizedResults = useMemo(() => {
    return results.map((result) => {
      const fileName =
        result.metadata?.fileName || result.metadata?.title || 'Untitled document';
      const fileExtension =
        result.metadata?.fileExtension ||
        (fileName.includes('.') ? fileName.split('.').pop()?.toLowerCase() : '') ||
        '';
      const uploadedAt = result.metadata?.uploadedAt || '';
      const folder = result.metadata?.folder || 'Uploads';
      const tags = Array.isArray(result.metadata?.tags) ? result.metadata?.tags : [];

      return {
        ...result,
        fileName,
        fileExtension,
        uploadedAt,
        folder,
        tags,
      };
    });
  }, [results]);

  const fileTypes = useMemo(() => {
    return Array.from(
      new Set(normalizedResults.map((result) => result.fileExtension).filter(Boolean)),
    ).sort();
  }, [normalizedResults]);

  const folders = useMemo(() => {
    return Array.from(new Set(normalizedResults.map((result) => result.folder))).sort();
  }, [normalizedResults]);

  const tags = useMemo(() => {
    return Array.from(
      new Set(normalizedResults.flatMap((result) => result.tags).filter(Boolean)),
    ).sort();
  }, [normalizedResults]);

  const filteredResults = useMemo(() => {
    return normalizedResults.filter((result) => {
      const hasType =
        selectedTypes.length === 0 || selectedTypes.includes(result.fileExtension);
      const hasFolder =
        selectedFolders.length === 0 || selectedFolders.includes(result.folder);
      const hasTag =
        selectedTags.length === 0 ||
        result.tags.some((tag) => selectedTags.includes(tag));
      const hasDate =
        selectedDates.length === 0 ||
        (result.uploadedAt &&
          selectedDates.some((range) => isInDateRange(new Date(result.uploadedAt), range)));

      return hasType && hasFolder && hasTag && hasDate;
    });
  }, [normalizedResults, selectedTypes, selectedFolders, selectedTags, selectedDates]);

  const clearAll = () => {
    setSelectedTypes([]);
    setSelectedDates([]);
    setSelectedFolders([]);
    setSelectedTags([]);
    updateParam('uploadTypes', []);
    updateParam('uploadDates', []);
    updateParam('uploadFolders', []);
    updateParam('uploadTags', []);
  };

  return (
    <div className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-100 dark:bg-dark-100 p-3 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-medium text-black dark:text-white">
          <Filter className="h-4 w-4 text-sky-500" />
          <span>Facettenfilter</span>
        </div>
        <button
          type="button"
          onClick={clearAll}
          className="text-xs font-medium text-black/60 dark:text-white/60 hover:text-black dark:hover:text-white"
        >
          Filter zurücksetzen
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs text-black/60 dark:text-white/60">
        <span className="font-medium text-black/70 dark:text-white/70">Schnellzugriff:</span>
        {DATE_PRESETS.filter((preset) => preset.id !== 'older').map((preset) => (
          <button
            key={preset.id}
            type="button"
            onClick={() => {
              const next = toggleValue(selectedDates, preset.id);
              setSelectedDates(next);
              updateParam('uploadDates', next);
            }}
            className={cn(
              'rounded-full border px-2 py-0.5',
              selectedDates.includes(preset.id)
                ? 'border-sky-500 text-sky-600 dark:text-sky-300'
                : 'border-black/10 dark:border-white/10',
            )}
          >
            {preset.label}
          </button>
        ))}
        {fileTypes.slice(0, 2).map((type) => (
          <button
            key={type}
            type="button"
            onClick={() => {
              const next = toggleValue(selectedTypes, type);
              setSelectedTypes(next);
              updateParam('uploadTypes', next);
            }}
            className={cn(
              'rounded-full border px-2 py-0.5 uppercase',
              selectedTypes.includes(type)
                ? 'border-sky-500 text-sky-600 dark:text-sky-300'
                : 'border-black/10 dark:border-white/10',
            )}
          >
            {type}
          </button>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-black/70 dark:text-white/70">
              <Filter className="h-3.5 w-3.5" />
              <span>Dateityp</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {fileTypes.length === 0 && (
                <span className="text-xs text-black/40 dark:text-white/40">
                  Keine Dateitypen gefunden
                </span>
              )}
              {fileTypes.map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => {
                    const next = toggleValue(selectedTypes, type);
                    setSelectedTypes(next);
                    updateParam('uploadTypes', next);
                  }}
                  className={cn(
                    'inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs uppercase',
                    selectedTypes.includes(type)
                      ? 'border-sky-500 text-sky-600 dark:text-sky-300'
                      : 'border-black/10 dark:border-white/10 text-black/60 dark:text-white/60',
                  )}
                >
                  <FormatIcon format={type} size={12} />
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-black/70 dark:text-white/70">
              <Calendar className="h-3.5 w-3.5" />
              <span>Datum</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {DATE_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => {
                    const next = toggleValue(selectedDates, preset.id);
                    setSelectedDates(next);
                    updateParam('uploadDates', next);
                  }}
                  className={cn(
                    'rounded-md border px-2 py-1 text-xs',
                    selectedDates.includes(preset.id)
                      ? 'border-sky-500 text-sky-600 dark:text-sky-300'
                      : 'border-black/10 dark:border-white/10 text-black/60 dark:text-white/60',
                  )}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-black/70 dark:text-white/70">
              <Folder className="h-3.5 w-3.5" />
              <span>Ordner</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {folders.map((folder) => (
                <button
                  key={folder}
                  type="button"
                  onClick={() => {
                    const next = toggleValue(selectedFolders, folder);
                    setSelectedFolders(next);
                    updateParam('uploadFolders', next);
                  }}
                  className={cn(
                    'rounded-md border px-2 py-1 text-xs',
                    selectedFolders.includes(folder)
                      ? 'border-sky-500 text-sky-600 dark:text-sky-300'
                      : 'border-black/10 dark:border-white/10 text-black/60 dark:text-white/60',
                  )}
                >
                  {folder}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-black/70 dark:text-white/70">
              <Tag className="h-3.5 w-3.5" />
              <span>Tags</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {tags.length === 0 && (
                <span className="text-xs text-black/40 dark:text-white/40">
                  Keine Tags gefunden
                </span>
              )}
              {tags.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => {
                    const next = toggleValue(selectedTags, tag);
                    setSelectedTags(next);
                    updateParam('uploadTags', next);
                  }}
                  className={cn(
                    'rounded-md border px-2 py-1 text-xs',
                    selectedTags.includes(tag)
                      ? 'border-sky-500 text-sky-600 dark:text-sky-300'
                      : 'border-black/10 dark:border-white/10 text-black/60 dark:text-white/60',
                  )}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-black/60 dark:text-white/60">
            <span>{filteredResults.length} Treffer</span>
            <span>Gesamt: {normalizedResults.length}</span>
          </div>

          {filteredResults.length === 0 ? (
            <div className="rounded-md border border-dashed border-black/20 dark:border-white/10 p-4 text-sm text-black/60 dark:text-white/60">
              Keine Dokumente passen zu den aktuellen Filtern.
            </div>
          ) : (
            <div className="space-y-2">
              {filteredResults.map((result, idx) => (
                <div
                  key={`${result.fileName}-${idx}`}
                  className="rounded-lg border border-light-200 dark:border-dark-200 bg-light-primary dark:bg-dark-primary p-3"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 h-10 w-10 rounded-md bg-cyan-100 text-cyan-800 dark:bg-sky-500 dark:text-cyan-50 flex items-center justify-center">
                      <FormatIcon format={result.fileExtension} size={20} />
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-medium text-black dark:text-white">
                          {result.fileName}
                        </span>
                        {result.fileExtension && (
                          <span className="text-[10px] uppercase text-black/40 dark:text-white/40">
                            {result.fileExtension}
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-black/50 dark:text-white/50">
                        <span className="inline-flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(result.uploadedAt)}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Folder className="h-3 w-3" />
                          {result.folder}
                        </span>
                        {result.tags.length > 0 && (
                          <span className="inline-flex items-center gap-1">
                            <Tag className="h-3 w-3" />
                            {result.tags.slice(0, 3).join(', ')}
                            {result.tags.length > 3 ? '…' : ''}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-black/60 dark:text-white/60 line-clamp-2">
                        {result.content}
                      </p>
                    </div>
                  </div>
                  {result.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {result.tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full border border-black/10 dark:border-white/10 px-2 py-0.5 text-[10px] text-black/50 dark:text-white/50"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadSearchResultsPanel;
