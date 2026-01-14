/**
 * Audio Preview Card Component
 *
 * Displays audio sources with timecode and snippet preview.
 */

'use client';

import { Volume2, Timer, Play } from 'lucide-react';
import { LocalSource } from '@/lib/types';

interface AudioPreviewCardProps {
    source: LocalSource;
    index: number;
    onClick?: () => void;
}

const AudioPreviewCard = ({ source, index, onClick }: AudioPreviewCardProps) => {
    const handleClick = () => {
        if (onClick) onClick();
    };

    return (
        <div
            className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 cursor-pointer"
            onClick={handleClick}
        >
            <div className="flex items-center space-x-2">
                <div className="bg-purple-500/20 text-purple-500 p-1.5 rounded-lg">
                    <Volume2 size={14} />
                </div>
                <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis flex-1">
                    {source.filename}
                </p>
            </div>

            <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center space-x-1 text-purple-400">
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

            <div className="bg-purple-500/10 rounded-md p-2">
                <p className="text-xs text-purple-500/90 line-clamp-3">
                    &ldquo;{source.textSnippet}&rdquo;
                </p>
            </div>

            <div className="flex items-center justify-between text-xs text-black/40 dark:text-white/40">
                <div className="flex items-center space-x-1">
                    <Play size={10} />
                    <span>Audio abspielen</span>
                </div>
                <span>#{index + 1}</span>
            </div>
        </div>
    );
'use client';

import { Music } from 'lucide-react';
import PreviewCard from './PreviewCard';

interface AudioPreviewCardProps {
  title: string;
  href?: string;
  snippet?: string;
  timecodeStart?: string;
  timecodeEnd?: string;
  sourceLabel?: string;
  index: number;
}

const AudioPreviewCard = ({
  title,
  href,
  snippet,
  timecodeStart,
  timecodeEnd,
  sourceLabel,
  index,
}: AudioPreviewCardProps) => {
  return (
    <PreviewCard href={href}>
      <div className="flex items-center justify-between text-xs text-black/50 dark:text-white/50">
        <div className="flex items-center space-x-2">
          <div className="bg-purple-500/10 text-purple-500 p-1 rounded-md">
            <Music size={12} />
          </div>
          <span className="uppercase tracking-wide">Audio</span>
        </div>
        <span>#{index + 1}</span>
      </div>

      <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis">
        {title}
      </p>

      <div className="flex items-center space-x-2">
        <div className="flex-1 h-5 bg-purple-500/10 rounded-md flex items-center px-2">
          <div className="flex items-center space-x-0.5 h-full">
            {[3, 5, 7, 4, 8, 6, 5, 7, 3].map((h, i) => (
              <div
                key={i}
                className="w-0.5 bg-purple-400/70 rounded-full"
                style={{ height: `${h * 2}px` }}
              />
            ))}
          </div>
        </div>
        <div className="flex flex-col text-[10px] font-mono text-purple-400">
          <span>{timecodeStart ?? '00:00'}</span>
          {timecodeEnd && <span>→ {timecodeEnd}</span>}
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

export default AudioPreviewCard;
