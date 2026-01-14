/* eslint-disable @next/next/no-img-element */
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  Transition,
  TransitionChild,
} from '@headlessui/react';
import { File } from 'lucide-react';
import { Fragment, useState } from 'react';
import { Chunk } from '@/lib/types';

const MessageSources = ({ sources }: { sources: Chunk[] }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const closeModal = () => {
    setIsDialogOpen(false);
    document.body.classList.remove('overflow-hidden-scrollable');
  };

  const openModal = () => {
    setIsDialogOpen(true);
    document.body.classList.add('overflow-hidden-scrollable');
  };

  const renderPreview = (
    source: Chunk,
    index: number,
    className?: string,
  ) => {
    const url = source.metadata.url ?? '';
    const title = source.metadata.title || url || 'Untitled';
    const rawSnippet = source.content?.trim() ?? '';
    const snippet =
      rawSnippet.length > 120 ? `${rawSnippet.slice(0, 117)}...` : rawSnippet;
    const timecodeStart = source.metadata.timecodeStart;
    const timecodeEnd = source.metadata.timecodeEnd;
    const page = source.metadata.page;
    const totalPages = source.metadata.totalPages;
    const isFile = url.includes('file_id://');
    const displayHost = isFile
      ? 'Uploaded File'
      : url.replace(/.+\/\/|www.|\..+/g, '');

    return (
      <a
        className={`bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 font-medium ${className ?? ''}`}
        key={index}
        href={url}
        target="_blank"
      >
        <p className="dark:text-white text-xs overflow-hidden whitespace-nowrap text-ellipsis">
          {title}
        </p>
        {snippet && (
          <p className="text-[11px] text-black/60 dark:text-white/60 line-clamp-2">
            {snippet}
          </p>
        )}
        <div className="flex flex-row items-center justify-between">
          <div className="flex flex-row items-center space-x-1">
            {isFile ? (
              <div className="bg-dark-200 hover:bg-dark-100 transition duration-200 flex items-center justify-center w-6 h-6 rounded-full">
                <File size={12} className="text-white/70" />
              </div>
            ) : (
              <img
                src={`https://s2.googleusercontent.com/s2/favicons?domain_url=${url}`}
                width={16}
                height={16}
                alt="favicon"
                className="rounded-lg h-4 w-4"
              />
            )}
            <p className="text-xs text-black/50 dark:text-white/50 overflow-hidden whitespace-nowrap text-ellipsis">
              {displayHost}
            </p>
          </div>
          <div className="flex flex-row items-center space-x-1 text-black/50 dark:text-white/50 text-xs">
            <div className="bg-black/50 dark:bg-white/50 h-[4px] w-[4px] rounded-full" />
            <span>{index + 1}</span>
          </div>
        </div>
        {(page || timecodeStart) && (
          <div className="flex flex-wrap items-center gap-2 text-[10px] text-black/50 dark:text-white/50">
            {page && (
              <span>
                Seite {page}
                {totalPages ? `/${totalPages}` : ''}
              </span>
            )}
            {timecodeStart && (
              <span>
                {timecodeStart}
                {timecodeEnd ? `–${timecodeEnd}` : ''}
              </span>
            )}
          </div>
        )}
      </a>
    );
  };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
      {sources.slice(0, 3).map((source, i) => renderPreview(source, i))}
      {sources.length > 3 && (
        <button
          onClick={openModal}
          className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 font-medium"
        >
          <div className="flex flex-row items-center space-x-1">
            {sources.slice(3, 6).map((source, i) => {
              return source.metadata.url === 'File' ? (
                <div
                  key={i}
                  className="bg-dark-200 hover:bg-dark-100 transition duration-200 flex items-center justify-center w-6 h-6 rounded-full"
                >
                  <File size={12} className="text-white/70" />
                </div>
              ) : (
                <img
                  key={i}
                  src={`https://s2.googleusercontent.com/s2/favicons?domain_url=${source.metadata.url}`}
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
                <DialogPanel className="w-full max-w-md transform rounded-2xl bg-light-secondary dark:bg-dark-secondary border border-light-200 dark:border-dark-200 p-6 text-left align-middle shadow-xl transition-all">
                  <DialogTitle className="text-lg font-medium leading-6 dark:text-white">
                    Sources
                  </DialogTitle>
                  <div className="grid grid-cols-2 gap-2 overflow-auto max-h-[300px] mt-2 pr-2">
                    {sources.map((source, i) =>
                      renderPreview(
                        source,
                        i,
                        'bg-light-secondary hover:bg-light-200 dark:bg-dark-secondary dark:hover:bg-dark-200 border border-light-200 dark:border-dark-200',
                      ),
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
