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
  onClick?: () => void;
  testId?: string;
}

const ImagePreviewCard = ({
  title,
  href,
  snippet,
  ocrText,
  thumbnailUrl,
  sourceLabel,
  index,
  onClick,
  testId,
}: ImagePreviewCardProps) => {
  return (
    <PreviewCard href={href} onClick={onClick} testId={testId}>
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
        <p className="text-xs text-black/60 dark:text-white/60 line-clamp-2">
          {snippet}
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

export default ImagePreviewCard;
