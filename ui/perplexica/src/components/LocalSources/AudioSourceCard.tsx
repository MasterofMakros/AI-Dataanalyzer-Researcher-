/**
 * Audio Source Card Component
 * 
 * Displays an audio source with waveform icon, timecode, and play button.
 */

'use client';

import { Play, Music } from 'lucide-react';
import { LocalSource } from '@/lib/types';

interface AudioSourceCardProps {
    source: LocalSource;
    index: number;
    onClick?: () => void;
}

const AudioSourceCard = ({ source, index, onClick }: AudioSourceCardProps) => {
    const handlePlayClick = () => {
        if (onClick) onClick();
        console.log(`Play audio ${source.filename} from ${source.timecodeStart}`);
    };

    return (
        <div
            className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 cursor-pointer"
            onClick={handlePlayClick}
        >
            {/* Header */}
            <div className="flex items-center space-x-2">
                <div className="bg-purple-500/20 text-purple-500 p-1.5 rounded-lg">
                    <Music size={14} />
                </div>
                <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis flex-1">
                    {source.filename}
                </p>
            </div>

            {/* Timecode with waveform visual */}
            {source.timecodeStart && (
                <div className="flex items-center space-x-2">
                    <div className="flex-1 h-4 bg-purple-500/10 rounded-md flex items-center px-2">
                        {/* Simple waveform representation */}
                        <div className="flex items-center space-x-0.5 h-full">
                            {[3, 6, 4, 8, 5, 7, 4, 6, 3].map((h, i) => (
                                <div
                                    key={i}
                                    className="w-0.5 bg-purple-400/60 rounded-full"
                                    style={{ height: `${h * 2}px` }}
                                />
                            ))}
                        </div>
                    </div>
                    <span className="text-xs font-mono text-purple-400">
                        {source.timecodeStart}
                    </span>
                </div>
            )}

            {/* Text snippet */}
            <p className="text-xs text-black/60 dark:text-white/60 line-clamp-2">
                {source.textSnippet}
            </p>

            {/* Footer */}
            <div className="flex items-center justify-between text-xs text-black/40 dark:text-white/40">
                <div className="flex items-center space-x-1">
                    <Play size={10} />
                    <span>Transkript</span>
                </div>
                <span>#{index + 1}</span>
            </div>
        </div>
    );
};

export default AudioSourceCard;
