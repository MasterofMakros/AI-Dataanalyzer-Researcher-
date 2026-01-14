/**
 * Audio Preview Card Component
 *
 * Displays audio sources with timecode and snippet preview.
 */

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
