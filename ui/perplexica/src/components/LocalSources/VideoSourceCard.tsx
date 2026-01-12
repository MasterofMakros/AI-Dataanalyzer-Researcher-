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
        // TODO: Implement video player modal with start at timecode
        if (onClick) onClick();
        console.log(`Play video ${source.filename} from ${source.timecodeStart}`);
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

            {/* Timecode badge */}
            {source.timecodeStart && (
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <span className="bg-red-500/10 text-red-400 text-xs px-2 py-1 rounded-md font-mono">
                            {source.timecodeStart}
                        </span>
                        {source.timecodeEnd && (
                            <span className="text-xs text-black/40 dark:text-white/40">
                                → {source.timecodeEnd}
                            </span>
                        )}
                    </div>
                    <Play size={12} className="text-red-400" />
                </div>
            )}

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
