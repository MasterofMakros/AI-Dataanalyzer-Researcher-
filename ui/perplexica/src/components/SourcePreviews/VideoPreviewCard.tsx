/**
 * Video Preview Card Component
 *
 * Displays video sources with timecode and snippet preview.
 */

'use client';

import { Video, Timer, Play } from 'lucide-react';
import { LocalSource } from '@/lib/types';

interface VideoPreviewCardProps {
    source: LocalSource;
    index: number;
    onClick?: () => void;
}

const VideoPreviewCard = ({ source, index, onClick }: VideoPreviewCardProps) => {
    const handleClick = () => {
        if (onClick) onClick();
    };

    return (
        <div
            className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 cursor-pointer"
            onClick={handleClick}
        >
            <div className="flex items-center space-x-2">
                <div className="bg-red-500/20 text-red-500 p-1.5 rounded-lg">
                    <Video size={14} />
                </div>
                <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis flex-1">
                    {source.filename}
                </p>
            </div>

            <div className="relative rounded-md overflow-hidden bg-black/10 dark:bg-white/10 h-20">
                {source.thumbnailUrl ? (
                    <img
                        src={source.thumbnailUrl}
                        alt={source.filename}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-dark-100 to-dark-200">
                        <div className="bg-red-500/30 p-2 rounded-full">
                            <Play size={18} className="text-red-100" />
                        </div>
                    </div>
                )}
                {source.timecodeStart && (
                    <div className="absolute bottom-1 left-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded font-mono">
                        {source.timecodeStart}
                    </div>
                )}
            </div>

            <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center space-x-1 text-red-400">
                    <Timer size={10} />
                    <span className="font-mono">
                        {source.timecodeStart || '00:00'}
                        {source.timecodeEnd ? ` - ${source.timecodeEnd}` : ''}
                    </span>
                </div>
                {source.confidence ? (
                    <span className="text-black/40 dark:text-white/40">
                        {Math.round(source.confidence)}% Match
                    </span>
                ) : null}
            </div>

            <p className="text-xs text-black/70 dark:text-white/70 line-clamp-2 italic">
                &ldquo;{source.textSnippet}&rdquo;
            </p>

            <div className="flex items-center justify-between text-xs text-black/40 dark:text-white/40">
                <div className="flex items-center space-x-1">
                    <Play size={10} />
                    <span>Video starten</span>
                </div>
                <span>#{index + 1}</span>
            </div>
        </div>
    );
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
}: VideoPreviewCardProps) => {
  return (
    <PreviewCard href={href}>
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
