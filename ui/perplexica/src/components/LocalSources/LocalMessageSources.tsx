/**
 * Local Message Sources Component
 * 
 * Renders local sources from Neural Vault with appropriate cards
 * based on source type (video, audio, document, image).
 */

'use client';

import { useState, Fragment } from 'react';
import {
    Dialog,
    DialogPanel,
    DialogTitle,
    Transition,
    TransitionChild,
} from '@headlessui/react';
import { Database, X } from 'lucide-react';
import { LocalSource } from '@/lib/types';
import MediaPlayerModal from './MediaPlayerModal';
import {
    AudioPreviewCard,
    ImagePreviewCard,
    PdfPreviewCard,
    SourcePreviewModal,
    VideoPreviewCard,
} from '../SourcePreviews';

interface LocalMessageSourcesProps {
    sources: LocalSource[];
    onSourceClick?: (source: LocalSource) => void;
    query?: string;
}

const LocalMessageSources = ({ sources, onSourceClick, query = '' }: LocalMessageSourcesProps) => {
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [selectedSource, setSelectedSource] = useState<LocalSource | null>(null);
    const [isPreviewOpen, setIsPreviewOpen] = useState(false);
    const [isMediaOpen, setIsMediaOpen] = useState(false);

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
        if (onSourceClick) {
            onSourceClick(source);
        }

        closeModal();

        if (source.sourceType === 'audio' || source.sourceType === 'video') {
            setIsPreviewOpen(false);
            setIsMediaOpen(true);
        } else {
            setIsMediaOpen(false);
            setIsPreviewOpen(true);
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
                return <VideoPreviewCard key={source.id} {...props} />;
            case 'audio':
                return <AudioPreviewCard key={source.id} {...props} />;
            case 'image':
                return <ImagePreviewCard key={source.id} {...props} />;
            case 'document':
            default:
                return <PdfPreviewCard key={source.id} {...props} />;
        }
    };

    if (sources.length === 0) {
        return null;
    }

    return (
        <>
            {/* Header */}
            <div className="flex items-center space-x-2 mb-2">
                <Database size={14} className="text-blue-400" />
                <span className="text-xs font-medium text-black/60 dark:text-white/60">
                    Lokale Quellen ({sources.length})
                </span>
            </div>

            {/* Source grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                {sources.slice(0, 3).map((source, i) => renderSourceCard(source, i))}

                {sources.length > 3 && (
                    <button
                        onClick={openModal}
                        className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col items-center justify-center space-y-2"
                    >
                        <div className="flex -space-x-2">
                            {sources.slice(3, 6).map((source, i) => (
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
                            +{sources.length - 3} weitere
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

                                    <div className="grid grid-cols-2 gap-3 max-h-[60vh] overflow-y-auto pr-2">
                                        {sources.map((source, i) => renderSourceCard(source, i))}
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
