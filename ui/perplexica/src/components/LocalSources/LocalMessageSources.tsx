/**
 * Local Message Sources Component
 *
 * Renders local sources from Neural Vault with appropriate cards
 * based on source type (video, audio, document, image).
 */

'use client';

import { Fragment, useMemo, useState } from 'react';
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
import SourcePreviewModal from '../SourcePreviews/SourcePreviewModal';
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
  const [selectedSource, setSelectedSource] = useState<LocalSource | null>(null);
  const [isMediaModalOpen, setIsMediaModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);

  const previewSources = useMemo(() => sources.slice(0, 3), [sources]);

  const openModal = () => {
    setIsDialogOpen(true);
    document.body.classList.add('overflow-hidden-scrollable');
  };

  const closeModal = () => {
    setIsDialogOpen(false);
    document.body.classList.remove('overflow-hidden-scrollable');
  };

  const handleSourceClick = (source: LocalSource) => {
    if (source.sourceType === 'audio' || source.sourceType === 'video') {
      setSelectedSource(source);
      setIsMediaModalOpen(true);
      setIsPreviewModalOpen(false);
    } else {
      setSelectedSource(source);
      setIsPreviewModalOpen(true);
      setIsMediaModalOpen(false);
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

  if (sources.length === 0) {
    return null;
  }

  return (
    <>
      <div className="flex flex-col space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Database size={16} className="text-blue-400" />
            <p className="text-sm font-medium text-black dark:text-white">
              Lokale Quellen
            </p>
          </div>
          {sources.length > previewSources.length && (
            <button
              onClick={openModal}
              className="text-xs text-blue-500 hover:text-blue-600"
            >
              Alle anzeigen ({sources.length})
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          {previewSources.map((source, index) =>
            renderSourceCard(source, index),
          )}
        </div>
      </div>

      <Transition appear show={isDialogOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={closeModal}>
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" />
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
                <DialogPanel className="w-full max-w-5xl transform rounded-2xl bg-light-secondary dark:bg-dark-secondary border border-light-200 dark:border-dark-200 shadow-xl transition-all overflow-hidden">
                  <div className="flex items-center justify-between p-4 border-b border-light-200 dark:border-dark-200">
                    <DialogTitle className="text-lg font-medium dark:text-white">
                      Lokale Quellen
                    </DialogTitle>
                    <button
                      onClick={closeModal}
                      className="p-2 rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition"
                    >
                      <X size={18} className="text-black/50 dark:text-white/50" />
                    </button>
                  </div>
                  <div className="p-4 grid grid-cols-2 gap-4 max-h-[70vh] overflow-y-auto">
                    {sources.map((source, index) =>
                      renderSourceCard(source, index),
                    )}
                  </div>
                </DialogPanel>
              </TransitionChild>
            </div>
          </div>
        </Dialog>
      </Transition>

      <SourcePreviewModal
        isOpen={isPreviewModalOpen}
        onClose={() => setIsPreviewModalOpen(false)}
        source={selectedSource}
      />

      <MediaPlayerModal
        isOpen={isMediaModalOpen}
        onClose={() => setIsMediaModalOpen(false)}
        source={selectedSource}
        query={query}
      />
    </>
  );
};

export default LocalMessageSources;
