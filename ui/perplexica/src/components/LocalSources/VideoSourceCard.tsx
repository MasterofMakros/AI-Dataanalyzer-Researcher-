/**
 * Video Source Card Component
 * 
 * Displays a video source with thumbnail, timecode, and play button.
 * Clicking plays the video from the specific timecode.
 */

'use client';

import { Play, Video } from 'lucide-react';
import { LocalSource } from '@/lib/types';

interface VideoSourceCardProps {
    source: LocalSource;
    index: number;
    onClick?: () => void;
}

const VideoSourceCard = ({ source, index, onClick }: VideoSourceCardProps) => {
    const handlePlayClick = () => {
        if (onClick) onClick();
    };

    return (
        <div
            className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 cursor-pointer"
            onClick={handlePlayClick}
        >
            {/* Header with icon and filename */}
            <div className="flex items-center space-x-2">
                <div className="bg-red-500/20 text-red-500 p-1.5 rounded-lg">
                    <Video size={14} />
                </div>
                <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis flex-1">
                    {source.filename}
                </p>
            </div>

            {/* Timecode preview */}
            <div className="relative rounded-md overflow-hidden bg-black/10 dark:bg-white/10 h-20">
                {source.thumbnailUrl ? (
                    <img
                        src={source.thumbnailUrl}
                        alt={source.filename}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="flex items-center justify-center w-full h-full text-black/30 dark:text-white/30 text-xs">
                        Videovorschau
                    </div>
                )}
                <div className="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded font-mono">
                    {source.timecodeStart ?? '00:00'}
                    {source.timecodeEnd ? ` → ${source.timecodeEnd}` : ''}
                </div>
            </div>

            {/* Text snippet */}
            <p className="text-xs text-black/60 dark:text-white/60 line-clamp-2">
                {source.textSnippet}
            </p>

            {/* Footer */}
            <div className="flex items-center justify-between text-xs text-black/40 dark:text-white/40">
                <span>Lokale Datei</span>
                <span>#{index + 1}</span>
            </div>
        </div>
    );
};

export default VideoSourceCard;
