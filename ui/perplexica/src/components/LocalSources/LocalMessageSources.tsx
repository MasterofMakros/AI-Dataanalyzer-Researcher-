/**
 * Local Message Sources Component
 *
 * Renders local sources from Neural Vault with appropriate cards
 * based on source type (video, audio, document, image).
 */

'use client';

import { useMemo, useState, Fragment } from 'react';
import {
    Dialog,
    DialogPanel,
    DialogTitle,
    Transition,
    TransitionChild,
} from '@headlessui/react';
import { Database, Filter, X } from 'lucide-react';
import { LocalSource } from '@/lib/types';
import MediaPlayerModal from './MediaPlayerModal';
import { SourcePreviewModal } from '../SourcePreviews';
import VideoSourceCard from './VideoSourceCard';
import AudioSourceCard from './AudioSourceCard';
import DocumentSourceCard from './DocumentSourceCard';
import ImageSourceCard from './ImageSourceCard';

interface LocalMessageSourcesProps {
    sources: LocalSource[];
    query: string;
    onSourceClick?: (source: LocalSource) => void;
}

const LocalMessageSources = ({
    sources,
    query,
    onSourceClick,
}: LocalMessageSourcesProps) => {
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [selectedSource, setSelectedSource] = useState<LocalSource | null>(
        null,
    );
    const [isPreviewOpen, setIsPreviewOpen] = useState(false);
    const [isMediaOpen, setIsMediaOpen] = useState(false);
    const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
    const [selectedFolders, setSelectedFolders] = useState<string[]>([]);
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');

    const closeModal = () => {
        setIsDialogOpen(false);
        document.body.classList.remove('overflow-hidden-scrollable');
    };

    const openModal = () => {
        setIsDialogOpen(true);
        document.body.classList.add('overflow-hidden-scrollable');
    };

    const handleSourceClick = (source: LocalSource) => {
        setSelectedSource(source);
        closeModal();

        if (source.sourceType === 'audio' || source.sourceType === 'video') {
            setIsPreviewOpen(false);
            setIsMediaOpen(true);
        } else {
            setIsMediaOpen(false);
            setIsPreviewOpen(true);
        }

        if (onSourceClick) {
            onSourceClick(source);
        }
    };

    const renderSourceCard = (source: LocalSource, index: number) => {
        const props = {
            source,
            index,
            onClick: () => handleSourceClick(source),
        };

        switch (source.sourceType) {
            case 'video':
                return <VideoSourceCard key={source.id} {...props} />;
            case 'audio':
                return <AudioSourceCard key={source.id} {...props} />;
            case 'image':
                return <ImageSourceCard key={source.id} {...props} />;
            case 'document':
            default:
                return <DocumentSourceCard key={source.id} {...props} />;
        }
    };

    const resolveFolder = (source: LocalSource) => {
        if (source.folder) {
            return source.folder;
        }
        if (!source.filePath) {
            return '';
        }
        const normalizedPath = source.filePath.replace(/\\/g, '/');
        const parts = normalizedPath.split('/');
        parts.pop();
        return parts.join('/');
    };

    const getTypeKey = (source: LocalSource) => {
        const extension = source.fileExtension?.replace(/^\./, '').toLowerCase();
        return extension || source.sourceType.toLowerCase();
    };

    const getSourceDate = (source: LocalSource) =>
        source.fileModified || source.fileCreated || source.indexedAt || '';

    const typeOptions = useMemo(() => {
        const types = new Set<string>();
        sources.forEach((source) => {
            const key = getTypeKey(source);
            if (key) {
                types.add(key);
            }
        });
        return Array.from(types).sort((a, b) => a.localeCompare(b));
    }, [sources]);

    const folderOptions = useMemo(() => {
        const folders = new Set<string>();
        sources.forEach((source) => {
            const folder = resolveFolder(source);
            if (folder) {
                folders.add(folder);
            }
        });
        return Array.from(folders).sort((a, b) => a.localeCompare(b));
    }, [sources]);

    const tagOptions = useMemo(() => {
        const tags = new Set<string>();
        sources.forEach((source) => {
            source.tags?.forEach((tag) => {
                if (tag) {
                    tags.add(tag);
                }
            });
        });
        return Array.from(tags).sort((a, b) => a.localeCompare(b));
    }, [sources]);

    const filteredSources = useMemo(() => {
        return sources.filter((source) => {
            const typeKey = getTypeKey(source);
            const folder = resolveFolder(source);
            const sourceTags = source.tags || [];
            const sourceDate = getSourceDate(source);

            const matchesType =
                selectedTypes.length === 0 || selectedTypes.includes(typeKey);
            const matchesFolder =
                selectedFolders.length === 0 || selectedFolders.includes(folder);
            const matchesTags =
                selectedTags.length === 0 ||
                selectedTags.every((tag) => sourceTags.includes(tag));
            const matchesDate = (() => {
                if (!dateFrom && !dateTo) {
                    return true;
                }
                if (!sourceDate) {
                    return false;
                }
                const sourceTime = new Date(sourceDate).getTime();
                if (Number.isNaN(sourceTime)) {
                    return false;
                }
                if (dateFrom) {
                    const fromTime = new Date(dateFrom).getTime();
                    if (!Number.isNaN(fromTime) && sourceTime < fromTime) {
                        return false;
                    }
                }
                if (dateTo) {
                    const toTime =
                        new Date(dateTo).getTime() + 24 * 60 * 60 * 1000 - 1;
                    if (!Number.isNaN(toTime) && sourceTime > toTime) {
                        return false;
                    }
                }
                return true;
            })();

            return matchesType && matchesFolder && matchesTags && matchesDate;
        });
    }, [dateFrom, dateTo, selectedFolders, selectedTags, selectedTypes, sources]);

    const resetFilters = () => {
        setSelectedTypes([]);
        setSelectedFolders([]);
        setSelectedTags([]);
        setDateFrom('');
        setDateTo('');
    };

    if (sources.length === 0) {
        return null;
    }

    const hasActiveFilters =
        selectedTypes.length > 0 ||
        selectedFolders.length > 0 ||
        selectedTags.length > 0 ||
        dateFrom.length > 0 ||
        dateTo.length > 0;

    return (
        <>
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                    <Database size={14} className="text-blue-400" />
                    <span className="text-xs font-medium text-black/60 dark:text-white/60">
                        Lokale Quellen ({filteredSources.length}
                        {hasActiveFilters ? ` von ${sources.length}` : ''})
                    </span>
                </div>
                <button
                    onClick={openModal}
                    className="inline-flex items-center gap-1 text-xs text-blue-500 hover:text-blue-400 transition"
                    data-testid="local-sources-filter-button"
                >
                    <Filter size={12} />
                    Filter
                </button>
            </div>

            {/* Source grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                {filteredSources.slice(0, 3).map((source, i) =>
                    renderSourceCard(source, i),
                )}

                {filteredSources.length > 3 && (
                    <button
                        onClick={openModal}
                        className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col items-center justify-center space-y-2"
                    >
                        <div className="flex -space-x-2">
                            {filteredSources.slice(3, 6).map((source, i) => (
                                <div
                                    key={i}
                                    className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center border-2 border-light-100 dark:border-dark-100"
                                >
                                    <span className="text-xs text-blue-400">
                                        {source.sourceType[0].toUpperCase()}
                                    </span>
                                </div>
                            ))}
                        </div>
                        <p className="text-xs text-black/50 dark:text-white/50">
                            +{filteredSources.length - 3} weitere
                        </p>
                    </button>
                )}
            </div>

            {/* Dialog for all sources */}
            <Transition appear show={isDialogOpen} as={Fragment}>
                <Dialog as="div" className="relative z-50" onClose={closeModal}>
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
                    <div className="fixed inset-0 overflow-y-auto">
                        <div className="flex min-h-full items-center justify-center p-4">
                            <TransitionChild
                                as={Fragment}
                                enter="ease-out duration-200"
                                enterFrom="opacity-0 scale-95"
                                enterTo="opacity-100 scale-100"
                                leave="ease-in duration-100"
                                leaveFrom="opacity-100 scale-100"
                                leaveTo="opacity-0 scale-95"
                            >
                                <DialogPanel className="w-full max-w-2xl transform rounded-2xl bg-light-secondary dark:bg-dark-secondary border border-light-200 dark:border-dark-200 p-6 shadow-xl transition-all">
                                    <div className="flex items-center justify-between mb-4">
                                        <DialogTitle className="text-lg font-medium dark:text-white flex items-center space-x-2">
                                            <Database size={20} className="text-blue-400" />
                                            <span>Lokale Quellen</span>
                                        </DialogTitle>
                                        <button
                                            onClick={closeModal}
                                            className="p-1 rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition"
                                        >
                                            <X size={20} className="text-black/50 dark:text-white/50" />
                                        </button>
                                    </div>

                                    <div className="flex flex-col gap-4 lg:flex-row">
                                        <div
                                            className="lg:w-56 shrink-0 space-y-4 text-xs text-black/70 dark:text-white/70"
                                            data-testid="local-sources-filter-panel"
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="font-semibold text-black/80 dark:text-white/80">
                                                    Filter
                                                </span>
                                                {hasActiveFilters && (
                                                    <button
                                                        onClick={resetFilters}
                                                        className="text-xs text-blue-500 hover:text-blue-400 transition"
                                                    >
                                                        Zurücksetzen
                                                    </button>
                                                )}
                                            </div>

                                            <div className="space-y-2" data-testid="filter-group-type">
                                                <p className="font-medium text-black/80 dark:text-white/80">
                                                    Dateityp
                                                </p>
                                                <div className="space-y-1">
                                                    {typeOptions.length === 0 && (
                                                        <p className="text-xs text-black/40 dark:text-white/40">
                                                            Keine Typen verfügbar
                                                        </p>
                                                    )}
                                                    {typeOptions.map((type) => (
                                                        <label
                                                            key={type}
                                                            className="flex items-center gap-2"
                                                        >
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedTypes.includes(type)}
                                                                onChange={(event) => {
                                                                    setSelectedTypes((prev) =>
                                                                        event.target.checked
                                                                            ? [...prev, type]
                                                                            : prev.filter(
                                                                                  (value) =>
                                                                                      value !== type,
                                                                              ),
                                                                    );
                                                                }}
                                                                className="rounded border-light-200 dark:border-dark-200"
                                                            />
                                                            <span>{type}</span>
                                                        </label>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="space-y-2" data-testid="filter-group-folder">
                                                <p className="font-medium text-black/80 dark:text-white/80">
                                                    Ordner
                                                </p>
                                                <div className="space-y-1">
                                                    {folderOptions.length === 0 && (
                                                        <p className="text-xs text-black/40 dark:text-white/40">
                                                            Keine Ordner verfügbar
                                                        </p>
                                                    )}
                                                    {folderOptions.map((folder) => (
                                                        <label
                                                            key={folder}
                                                            className="flex items-center gap-2"
                                                        >
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedFolders.includes(folder)}
                                                                onChange={(event) => {
                                                                    setSelectedFolders((prev) =>
                                                                        event.target.checked
                                                                            ? [...prev, folder]
                                                                            : prev.filter(
                                                                                  (value) =>
                                                                                      value !== folder,
                                                                              ),
                                                                    );
                                                                }}
                                                                className="rounded border-light-200 dark:border-dark-200"
                                                            />
                                                            <span className="truncate" title={folder}>
                                                                {folder}
                                                            </span>
                                                        </label>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="space-y-2" data-testid="filter-group-tag">
                                                <p className="font-medium text-black/80 dark:text-white/80">
                                                    Tags
                                                </p>
                                                <div className="space-y-1">
                                                    {tagOptions.length === 0 && (
                                                        <p className="text-xs text-black/40 dark:text-white/40">
                                                            Keine Tags verfügbar
                                                        </p>
                                                    )}
                                                    {tagOptions.map((tag) => (
                                                        <label key={tag} className="flex items-center gap-2">
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedTags.includes(tag)}
                                                                onChange={(event) => {
                                                                    setSelectedTags((prev) =>
                                                                        event.target.checked
                                                                            ? [...prev, tag]
                                                                            : prev.filter(
                                                                                  (value) =>
                                                                                      value !== tag,
                                                                              ),
                                                                    );
                                                                }}
                                                                className="rounded border-light-200 dark:border-dark-200"
                                                            />
                                                            <span>{tag}</span>
                                                        </label>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="space-y-2" data-testid="filter-group-date">
                                                <p className="font-medium text-black/80 dark:text-white/80">
                                                    Zeitraum
                                                </p>
                                                <div className="space-y-2">
                                                    <label className="flex flex-col gap-1">
                                                        <span className="text-[11px] text-black/50 dark:text-white/50">
                                                            Von
                                                        </span>
                                                        <input
                                                            type="date"
                                                            value={dateFrom}
                                                            onChange={(event) =>
                                                                setDateFrom(event.target.value)
                                                            }
                                                            className="rounded border border-light-200 dark:border-dark-200 bg-transparent px-2 py-1 text-xs"
                                                        />
                                                    </label>
                                                    <label className="flex flex-col gap-1">
                                                        <span className="text-[11px] text-black/50 dark:text-white/50">
                                                            Bis
                                                        </span>
                                                        <input
                                                            type="date"
                                                            value={dateTo}
                                                            onChange={(event) =>
                                                                setDateTo(event.target.value)
                                                            }
                                                            className="rounded border border-light-200 dark:border-dark-200 bg-transparent px-2 py-1 text-xs"
                                                        />
                                                    </label>
                                                </div>
                                            </div>

                                            <div
                                                className="text-[11px] text-black/50 dark:text-white/50"
                                                data-testid="local-sources-result-count"
                                            >
                                                {filteredSources.length} Treffer
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-3 max-h-[60vh] overflow-y-auto pr-2 flex-1">
                                            {filteredSources.length === 0 ? (
                                                <div className="col-span-2 text-center text-sm text-black/50 dark:text-white/50 py-10">
                                                    Keine Quellen entsprechen den aktiven Filtern.
                                                </div>
                                            ) : (
                                                filteredSources.map((source, i) =>
                                                    renderSourceCard(source, i),
                                                )
                                            )}
                                        </div>
                                    </div>
                                </DialogPanel>
                            </TransitionChild>
                        </div>
                    </div>
                </Dialog>
            </Transition>

            <SourcePreviewModal
                isOpen={isPreviewOpen}
                onClose={() => setIsPreviewOpen(false)}
                source={selectedSource}
            />

            <MediaPlayerModal
                isOpen={isMediaOpen}
                onClose={() => setIsMediaOpen(false)}
                source={selectedSource}
                query={query}
            />
        </>
    );
};

export default LocalMessageSources;
