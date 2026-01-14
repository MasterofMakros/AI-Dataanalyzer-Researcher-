/* eslint-disable @next/next/no-img-element */
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  Transition,
  TransitionChild,
} from '@headlessui/react';
import { File } from 'lucide-react';
import { Fragment, useMemo, useState } from 'react';
import { Chunk } from '@/lib/types';
import {
  AudioPreviewCard,
  ImagePreviewCard,
  PdfPreviewCard,
  VideoPreviewCard,
} from './SourcePreviews';
import {
  formatTimestamp,
  getSourcePreviewType,
  SourcePreviewType,
} from './SourcePreviews/previewUtils';

const getSourceLabel = (source: Chunk) => {
  const url = source.metadata?.url || '';
  if (url.includes('file_id://')) return 'Uploaded File';
  if (!url) return undefined;
  return url.replace(/.+\/\/|www\.|\..+/g, '');
};

const MessageSources = ({ sources }: { sources: Chunk[] }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

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

  const renderPreviewCard = (
    source: Chunk,
    type: SourcePreviewType,
    index: number,
  ) => {
    const title = source.metadata?.title || 'Untitled source';
    const href = source.metadata?.url;
    const snippet = source.content;
    const sourceLabel = getSourceLabel(source);
    const evidence = source.evidence?.[0];
    const pageNumber = source.metadata?.page ?? evidence?.page;
    const totalPages = source.metadata?.totalPages;
    const timecodeStart =
      source.metadata?.timecodeStart ??
      evidence?.timecodeStart ??
      formatTimestamp(source.metadata?.timestamp ?? evidence?.timestamp);
    const timecodeEnd = source.metadata?.timecodeEnd ?? evidence?.timecodeEnd;

    if (type === 'pdf') {
      return (
        <PdfPreviewCard
          key={index}
          title={title}
          href={href}
          snippet={snippet}
          pageNumber={pageNumber}
          totalPages={totalPages}
          sourceLabel={sourceLabel}
          index={index}
        />
      );
    }

    if (type === 'audio') {
      return (
        <AudioPreviewCard
          key={index}
          title={title}
          href={href}
          snippet={snippet}
          timecodeStart={timecodeStart}
          timecodeEnd={timecodeEnd}
          sourceLabel={sourceLabel}
          index={index}
        />
      );
    }

    if (type === 'video') {
      return (
        <VideoPreviewCard
          key={index}
          title={title}
          href={href}
          snippet={snippet}
          timecodeStart={timecodeStart}
          timecodeEnd={timecodeEnd}
          thumbnailUrl={source.metadata?.thumbnailUrl}
          sourceLabel={sourceLabel}
          index={index}
        />
      );
    }

    if (type === 'image') {
      return (
        <ImagePreviewCard
          key={index}
          title={title}
          href={href}
          snippet={snippet}
          ocrText={source.metadata?.ocrText}
          thumbnailUrl={source.metadata?.thumbnailUrl}
          sourceLabel={sourceLabel}
          index={index}
        />
      );
    }

    const fallbackContent = (
      <>
        <p className="dark:text-white text-xs overflow-hidden whitespace-nowrap text-ellipsis">
          {title}
        </p>
        <div className="flex flex-row items-center justify-between">
          <div className="flex flex-row items-center space-x-1">
            {href?.includes('file_id://') ? (
              <div className="bg-dark-200 hover:bg-dark-100 transition duration-200 flex items-center justify-center w-6 h-6 rounded-full">
                <File size={12} className="text-white/70" />
              </div>
            ) : (
              <img
                src={`https://s2.googleusercontent.com/s2/favicons?domain_url=${href}`}
                width={16}
                height={16}
                alt="favicon"
                className="rounded-lg h-4 w-4"
              />
            )}
            <p className="text-xs text-black/50 dark:text-white/50 overflow-hidden whitespace-nowrap text-ellipsis">
              {getSourceLabel(source)}
            </p>
          </div>
          <div className="flex flex-row items-center space-x-1 text-black/50 dark:text-white/50 text-xs">
            <div className="bg-black/50 dark:bg-white/50 h-[4px] w-[4px] rounded-full" />
            <span>{index + 1}</span>
          </div>
        </div>
      </>
    );

    if (!href) {
      return (
        <div
          className="bg-light-100 dark:bg-dark-100 rounded-lg p-3 flex flex-col space-y-2 font-medium"
          key={index}
        >
          {fallbackContent}
        </div>
      );
    }

    return (
      <a
        className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 font-medium"
        key={index}
        href={href}
        target="_blank"
        rel="noreferrer"
      >
        {fallbackContent}
      </a>
    );
  };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
      {previewSources.slice(0, 3).map(({ source, type }, i) =>
        renderPreviewCard(source, type, i),
      )}
      {sources.length > 3 && (
        <button
          onClick={openModal}
          className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 font-medium"
        >
          <div className="flex flex-row items-center space-x-1">
            {previewSources.slice(3, 6).map(({ source }, i) => {
              return source.metadata?.url?.includes('file_id://') ? (
                <div
                  key={i}
                  className="bg-dark-200 hover:bg-dark-100 transition duration-200 flex items-center justify-center w-6 h-6 rounded-full"
                >
                  <File size={12} className="text-white/70" />
                </div>
              ) : (
                <img
                  key={i}
                  src={`https://s2.googleusercontent.com/s2/favicons?domain_url=${source.metadata?.url}`}
                  width={16}
                  height={16}
                  alt="favicon"
                  className="rounded-lg h-4 w-4"
                />
              );
            })}
          </div>
          <p className="text-xs text-black/50 dark:text-white/50">
            View {sources.length - 3} more
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
    </div>
  );
};

export default MessageSources;
