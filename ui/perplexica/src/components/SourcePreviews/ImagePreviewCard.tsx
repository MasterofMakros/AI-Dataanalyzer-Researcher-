/**
 * Image Preview Card Component
 *
 * Displays image sources with thumbnails and OCR highlight.
 */

'use client';

import { Image as ImageIcon, Type, Maximize2 } from 'lucide-react';
import { LocalSource } from '@/lib/types';

interface ImagePreviewCardProps {
    source: LocalSource;
    index: number;
    onClick?: () => void;
}

const ImagePreviewCard = ({ source, index, onClick }: ImagePreviewCardProps) => {
    const handleClick = () => {
        if (onClick) onClick();
    };

    return (
        <div
            className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 cursor-pointer"
            onClick={handleClick}
        >
            <div className="flex items-center space-x-2">
                <div className="bg-emerald-500/20 text-emerald-500 p-1.5 rounded-lg">
                    <ImageIcon size={14} />
                </div>
                <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis flex-1">
                    {source.filename}
                </p>
            </div>

            <div className="relative bg-black/10 dark:bg-white/10 rounded-md h-20 flex items-center justify-center overflow-hidden">
                {source.thumbnailUrl ? (
                    <img
                        src={source.thumbnailUrl}
                        alt={source.filename}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="flex flex-col items-center space-y-1 text-black/30 dark:text-white/30">
                        <ImageIcon size={24} />
                        <span className="text-xs">Vorschau</span>
                    </div>
                )}

                <div className="absolute top-1 right-1 bg-black/60 text-white px-1.5 py-0.5 rounded text-xs flex items-center space-x-1">
                    <Type size={10} />
                    <span>OCR</span>
                </div>
            </div>

            {source.ocrText ? (
                <div className="bg-emerald-500/10 rounded-md p-2">
                    <p className="text-xs text-emerald-600 dark:text-emerald-400 line-clamp-2 font-mono">
                        {source.ocrText}
                    </p>
                </div>
            ) : (
                <p className="text-xs text-black/60 dark:text-white/60 line-clamp-2">
                    {source.textSnippet}
                </p>
            )}

            <div className="flex items-center justify-between text-xs text-black/40 dark:text-white/40">
                <div className="flex items-center space-x-1">
                    <Maximize2 size={10} />
                    <span>Bild ansehen</span>
                </div>
                <span>#{index + 1}</span>
            </div>
        </div>
    );
'use client';

import { Image as ImageIcon, Type } from 'lucide-react';
import PreviewCard from './PreviewCard';

interface ImagePreviewCardProps {
  title: string;
  href?: string;
  snippet?: string;
  ocrText?: string;
  thumbnailUrl?: string;
  sourceLabel?: string;
  index: number;
}

const ImagePreviewCard = ({
  title,
  href,
  snippet,
  ocrText,
  thumbnailUrl,
  sourceLabel,
  index,
}: ImagePreviewCardProps) => {
  return (
    <PreviewCard href={href}>
      <div className="flex items-center justify-between text-xs text-black/50 dark:text-white/50">
        <div className="flex items-center space-x-2">
          <div className="bg-emerald-500/10 text-emerald-500 p-1 rounded-md">
            <ImageIcon size={12} />
          </div>
          <span className="uppercase tracking-wide">Bild</span>
        </div>
        <span>#{index + 1}</span>
      </div>

      <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis">
        {title}
      </p>

      <div className="relative rounded-md overflow-hidden bg-black/10 dark:bg-white/10 h-20">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex items-center justify-center w-full h-full text-black/30 dark:text-white/30 text-xs">
            Bildvorschau
          </div>
        )}
        {ocrText && (
          <div className="absolute top-1 right-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded flex items-center space-x-1">
            <Type size={10} />
            <span>OCR</span>
          </div>
        )}
      </div>

      {ocrText ? (
        <div className="bg-emerald-500/10 rounded-md p-2">
          <p className="text-xs text-emerald-600 dark:text-emerald-400 line-clamp-2 font-mono">
            {ocrText}
          </p>
        </div>
      ) : (
        snippet && (
          <p className="text-xs text-black/60 dark:text-white/60 line-clamp-2">
            {snippet}
          </p>
        )
      )}

      {sourceLabel && (
        <div className="text-[11px] text-black/40 dark:text-white/40">
          {sourceLabel}
        </div>
      )}
    </PreviewCard>
  );
};

export default ImagePreviewCard;
