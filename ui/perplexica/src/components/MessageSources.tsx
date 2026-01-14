/* eslint-disable @next/next/no-img-element */
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  Transition,
  TransitionChild,
} from '@headlessui/react';
import { FileText, Globe, Image as ImageIcon, Music, Video } from 'lucide-react';
import { Fragment, useMemo, useState } from 'react';
import { Chunk } from '@/lib/types';
import {
  AudioPreviewCard,
  ImagePreviewCard,
  PdfPreviewCard,
  VideoPreviewCard,
} from './SourcePreviews';
import PreviewCard from './SourcePreviews/PreviewCard';
import SourcePreviewModal, {
  SourcePreview,
} from './SourcePreviews/SourcePreviewModal';
import {
  formatTimestamp,
  getSourcePreviewType,
  SourcePreviewType,
} from './SourcePreviews/previewUtils';

const typeIconMap: Record<SourcePreviewType, JSX.Element> = {
  pdf: <FileText size={12} />,
  audio: <Music size={12} />,
  video: <Video size={12} />,
  image: <ImageIcon size={12} />,
  web: <Globe size={12} />,
};

const getSourceLabel = (source: Chunk) => {
  const url = source.metadata?.url || '';
  if (url.includes('file_id://')) return 'Uploaded File';
  if (!url) return undefined;
  return url.replace(/.+\/\/|www\.|\..+/g, '');
};

const MessageSources = ({ sources }: { sources: Chunk[] }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [previewSource, setPreviewSource] = useState<SourcePreview | null>(
    null,
  );

  const previewSources = useMemo(
    () =>
      sources.map((source) => ({
        source,
        type: getSourcePreviewType(source.metadata),
      })),
    [sources],
  );

  const closeModal = () => {
    setIsDialogOpen(false);
    document.body.classList.remove('overflow-hidden-scrollable');
  };

  const openModal = () => {
    setIsDialogOpen(true);
    document.body.classList.add('overflow-hidden-scrollable');
  };

  const openPreview = (data: SourcePreview) => {
    setPreviewSource(data);
    setIsPreviewOpen(true);
  };

  const closePreview = () => {
    setIsPreviewOpen(false);
    setPreviewSource(null);
  };

  const buildPreviewSource = (
    source: Chunk,
    type: SourcePreviewType,
  ): SourcePreview => {
    const title = source.metadata?.title || 'Untitled source';
    const href = source.metadata?.url;
    const snippet = source.content;
    const sourceLabel = getSourceLabel(source);
    const evidence = source.evidence?.[0];
    const pageNumber = source.metadata?.page ?? evidence?.page;
    const totalPages = source.metadata?.totalPages;
    const timestampStart =
      source.metadata?.timestampStart ??
      evidence?.timestampStart ??
      source.metadata?.timestamp ??
      evidence?.timestamp;
    const timestampEnd =
      source.metadata?.timestampEnd ?? evidence?.timestampEnd ?? undefined;
    const timecodeStart =
      source.metadata?.timecodeStart ??
      evidence?.timecodeStart ??
      formatTimestamp(timestampStart);
    const timecodeEnd =
      source.metadata?.timecodeEnd ??
      evidence?.timecodeEnd ??
      formatTimestamp(timestampEnd);

    return {
      title,
      href,
      snippet,
      type,
      pageNumber,
      totalPages,
      timecodeStart,
      timecodeEnd,
      timestampStart,
      timestampEnd,
      thumbnailUrl: source.metadata?.thumbnailUrl,
      ocrText: source.metadata?.ocrText,
      sourceLabel,
    };
  };

  const renderPreviewCard = (
    source: Chunk,
    type: SourcePreviewType,
    index: number,
  ) => {
    const preview = buildPreviewSource(source, type);
    const handleClick = () => openPreview(preview);

    if (type === 'pdf') {
      return (
        <PdfPreviewCard
          key={index}
          title={preview.title}
          href={preview.href}
          snippet={preview.snippet}
          pageNumber={preview.pageNumber}
          totalPages={preview.totalPages}
          sourceLabel={preview.sourceLabel}
          index={index}
          onClick={handleClick}
        />
      );
    }

    if (type === 'audio') {
      return (
        <AudioPreviewCard
          key={index}
          title={preview.title}
          href={preview.href}
          snippet={preview.snippet}
          timecodeStart={preview.timecodeStart}
          timecodeEnd={preview.timecodeEnd}
          sourceLabel={preview.sourceLabel}
          index={index}
          onClick={handleClick}
        />
      );
    }

    if (type === 'video') {
      return (
        <VideoPreviewCard
          key={index}
          title={preview.title}
          href={preview.href}
          snippet={preview.snippet}
          timecodeStart={preview.timecodeStart}
          timecodeEnd={preview.timecodeEnd}
          thumbnailUrl={preview.thumbnailUrl}
          sourceLabel={preview.sourceLabel}
          index={index}
          onClick={handleClick}
        />
      );
    }

    if (type === 'image') {
      return (
        <ImagePreviewCard
          key={index}
          title={preview.title}
          href={preview.href}
          snippet={preview.snippet}
          ocrText={preview.ocrText}
          thumbnailUrl={preview.thumbnailUrl}
          sourceLabel={preview.sourceLabel}
          index={index}
          onClick={handleClick}
        />
      );
    }

    return (
      <PreviewCard key={index} onClick={handleClick}>
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
          {preview.title}
        </p>
        {preview.snippet && (
          <p className="text-xs text-black/70 dark:text-white/70 line-clamp-2">
            {preview.snippet}
          </p>
        )}
        {preview.sourceLabel && (
          <div className="text-[11px] text-black/40 dark:text-white/40">
            {preview.sourceLabel}
          </div>
        )}
      </PreviewCard>
    );
  };

  const visibleSources = previewSources.slice(0, 4);
  const remainingSources = previewSources.length - visibleSources.length;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
      {visibleSources.map(({ source, type }, i) =>
        renderPreviewCard(source, type, i),
      )}
      {remainingSources > 0 && (
        <button
          onClick={openModal}
          className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 font-medium"
        >
          <div className="flex flex-row items-center space-x-1">
            {previewSources.slice(4, 7).map(({ type }, i) => (
              <div
                key={`${type}-${i}`}
                className="bg-black/5 dark:bg-white/10 flex items-center justify-center w-6 h-6 rounded-full"
              >
                {typeIconMap[type]}
              </div>
            ))}
          </div>
          <p className="text-xs text-black/50 dark:text-white/50">
            View {remainingSources} more
          </p>
        </button>
      )}
      <Transition appear show={isDialogOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={closeModal}>
          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <TransitionChild
                as={Fragment}
                enter="ease-out duration-200"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-100"
                leaveFrom="opacity-100 scale-200"
                leaveTo="opacity-0 scale-95"
              >
                <DialogPanel className="w-full max-w-4xl transform rounded-2xl bg-light-secondary dark:bg-dark-secondary border border-light-200 dark:border-dark-200 p-6 text-left align-middle shadow-xl transition-all">
                  <DialogTitle className="text-lg font-medium leading-6 dark:text-white">
                    Sources
                  </DialogTitle>
                  <div className="grid grid-cols-2 gap-2 overflow-auto max-h-[70vh] mt-4 pr-2">
                    {previewSources.map(({ source, type }, i) =>
                      renderPreviewCard(source, type, i),
                    )}
                  </div>
                </DialogPanel>
              </TransitionChild>
            </div>
          </div>
        </Dialog>
      </Transition>
      <SourcePreviewModal
        isOpen={isPreviewOpen}
        onClose={closePreview}
        source={previewSource}
      />
    </div>
  );
};

export default MessageSources;
