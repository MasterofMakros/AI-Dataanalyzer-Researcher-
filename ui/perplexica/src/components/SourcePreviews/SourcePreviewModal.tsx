/**
 * Source Preview Modal
 *
 * Quick-view modal for PDF, image, audio, and video sources with
 * snippet/ocr highlights and timecodes.
 */

'use client';

import { Fragment } from 'react';
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  Transition,
  TransitionChild,
} from '@headlessui/react';
import {
  ExternalLink,
  FileText,
  Image as ImageIcon,
  Music,
  Video,
  X,
} from 'lucide-react';
import { formatTimestamp, SourcePreviewType } from './previewUtils';

export type SourcePreview = {
  title: string;
  type: SourcePreviewType;
  href?: string;
  snippet?: string;
  pageNumber?: number;
  totalPages?: number;
  timecodeStart?: string;
  timecodeEnd?: string;
  timestampStart?: number;
  timestampEnd?: number;
  thumbnailUrl?: string;
  ocrText?: string;
  sourceLabel?: string;
};

interface SourcePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  source: SourcePreview | null;
}

const typeConfig: Record<SourcePreviewType, { label: string; icon: JSX.Element; accent: string }> = {
  pdf: {
    label: 'PDF-Schnellansicht',
    icon: <FileText size={20} />,
    accent: 'bg-red-500/20 text-red-500',
  },
  image: {
    label: 'Bildvorschau',
    icon: <ImageIcon size={20} />,
    accent: 'bg-emerald-500/20 text-emerald-500',
  },
  audio: {
    label: 'Audio-Snippet',
    icon: <Music size={20} />,
    accent: 'bg-purple-500/20 text-purple-500',
  },
  video: {
    label: 'Video-Snippet',
    icon: <Video size={20} />,
    accent: 'bg-red-500/20 text-red-500',
  },
  web: {
    label: 'Web-Quelle',
    icon: <FileText size={20} />,
    accent: 'bg-sky-500/20 text-sky-500',
  },
};

const SourcePreviewModal = ({
  isOpen,
  onClose,
  source,
}: SourcePreviewModalProps) => {
  if (!source) return null;

  const config = typeConfig[source.type];
  const timecodeStart =
    source.timecodeStart ?? formatTimestamp(source.timestampStart);
  const timecodeEnd =
    source.timecodeEnd ?? formatTimestamp(source.timestampEnd);

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
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
              <DialogPanel className="w-full max-w-3xl transform rounded-2xl bg-light-secondary dark:bg-dark-secondary border border-light-200 dark:border-dark-200 shadow-xl transition-all overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-light-200 dark:border-dark-200">
                  <DialogTitle className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${config.accent}`}>
                      {config.icon}
                    </div>
                    <div>
                      <h3 className="text-lg font-medium dark:text-white truncate max-w-md">
                        {source.title}
                      </h3>
                      <p className="text-xs text-black/50 dark:text-white/50">
                        {config.label}
                        {source.pageNumber ? (
                          <>
                            {' '}
                            · Seite {source.pageNumber}
                            {source.totalPages
                              ? ` / ${source.totalPages}`
                              : ''}
                          </>
                        ) : null}
                        {timecodeStart ? (
                          <>
                            {' '}
                            · {timecodeStart}
                            {timecodeEnd ? `–${timecodeEnd}` : ''}
                          </>
                        ) : null}
                        {source.sourceLabel ? ` · ${source.sourceLabel}` : ''}
                      </p>
                    </div>
                  </DialogTitle>
                  <div className="flex items-center space-x-2">
                    {source.href && (
                      <a
                        href={source.href}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center space-x-1 text-xs text-blue-400 hover:text-blue-300"
                      >
                        <ExternalLink size={12} />
                        <span>Quelle öffnen</span>
                      </a>
                    )}
                    <button
                      onClick={onClose}
                      className="p-2 rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition"
                    >
                      <X size={20} className="text-black/50 dark:text-white/50" />
                    </button>
                  </div>
                </div>

                <div className="p-6 space-y-4">
                  {(source.thumbnailUrl || source.type === 'image') && (
                    <div className="rounded-lg overflow-hidden bg-black/10 dark:bg-white/10">
                      {source.thumbnailUrl ? (
                        <img
                          src={source.thumbnailUrl}
                          alt={source.title}
                          className="w-full max-h-[360px] object-contain bg-black/80"
                        />
                      ) : (
                        <div className="h-48 flex items-center justify-center text-black/40 dark:text-white/40">
                          Keine Vorschau verfügbar
                        </div>
                      )}
                    </div>
                  )}

                  {source.ocrText && (
                    <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3">
                      <p className="text-xs text-emerald-600 dark:text-emerald-300 font-mono whitespace-pre-wrap">
                        {source.ocrText}
                      </p>
                    </div>
                  )}

                  {source.snippet && (
                    <div className="bg-black/5 dark:bg-white/5 rounded-lg p-4">
                      <p className="text-sm text-black/70 dark:text-white/70 leading-relaxed">
                        &ldquo;{source.snippet}&rdquo;
                      </p>
                    </div>
                  )}

                  {!source.snippet && source.type !== 'image' && (
                    <div className="bg-black/5 dark:bg-white/5 rounded-lg p-4">
                      <p className="text-sm text-black/70 dark:text-white/70 leading-relaxed">
                        Keine Vorschau verfügbar.
                      </p>
                    </div>
                  )}
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default SourcePreviewModal;
