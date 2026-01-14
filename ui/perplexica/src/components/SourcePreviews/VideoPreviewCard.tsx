'use client';

import { Video } from 'lucide-react';
import PreviewCard from './PreviewCard';

interface VideoPreviewCardProps {
  title: string;
  href?: string;
  snippet?: string;
  timecodeStart?: string;
  timecodeEnd?: string;
  thumbnailUrl?: string;
  sourceLabel?: string;
  index: number;
  onClick?: () => void;
}

const VideoPreviewCard = ({
  title,
  href,
  snippet,
  timecodeStart,
  timecodeEnd,
  thumbnailUrl,
  sourceLabel,
  index,
  onClick,
}: VideoPreviewCardProps) => {
  return (
    <PreviewCard href={href} onClick={onClick}>
      <div className="flex items-center justify-between text-xs text-black/50 dark:text-white/50">
        <div className="flex items-center space-x-2">
          <div className="bg-red-500/10 text-red-500 p-1 rounded-md">
            <Video size={12} />
          </div>
          <span className="uppercase tracking-wide">Video</span>
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
            Videovorschau
          </div>
        )}
        <div className="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded font-mono">
          {timecodeStart ?? '00:00'}
          {timecodeEnd ? ` → ${timecodeEnd}` : ''}
        </div>
      </div>

      {snippet && (
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

export default VideoPreviewCard;
