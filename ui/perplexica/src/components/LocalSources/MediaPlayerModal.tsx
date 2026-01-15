/**
 * Media Player Modal Component
 * 
 * Full-screen modal with video/audio player, timecode seeking,
 * and transcript overlay with highlighted search matches.
 */

'use client';

import { useEffect, useRef, useState, Fragment } from 'react';
import {
    Dialog,
    DialogPanel,
    DialogTitle,
    Transition,
    TransitionChild,
} from '@headlessui/react';
import {
    X,
    Play,
    Pause,
    SkipBack,
    SkipForward,
    Volume2,
    Video,
} from 'lucide-react';
import { LocalSource } from '@/lib/types';
import { getMediaStreamUrl } from '@/lib/neuralVault';

interface MediaPlayerModalProps {
    isOpen: boolean;
    onClose: () => void;
    source: LocalSource | null;
    query: string;
}

const MediaPlayerModal = ({ isOpen, onClose, source, query }: MediaPlayerModalProps) => {
    const mediaRef = useRef<HTMLVideoElement | HTMLAudioElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);

    // Parse timecode to seconds
    const parseTimecode = (tc: string | undefined): number => {
        if (!tc) return 0;
        const parts = tc.split(':').map(Number);
        if (parts.length === 3) {
            return parts[0] * 3600 + parts[1] * 60 + parts[2];
        }
        if (parts.length === 2) {
            return parts[0] * 60 + parts[1];
        }
        return 0;
    };

    // Format seconds to timecode
    const formatTime = (seconds: number): string => {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        if (h > 0) {
            return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    // Get start time from source
    const startTime = parseTimecode(source?.timecodeStart);

    useEffect(() => {
        if (isOpen && mediaRef.current && source) {
            // Set start time when modal opens
            mediaRef.current.currentTime = startTime;
            setCurrentTime(startTime);
        }
    }, [isOpen, source, startTime]);

    const handlePlayPause = () => {
        if (mediaRef.current) {
            if (isPlaying) {
                mediaRef.current.pause();
            } else {
                mediaRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    const handleSeek = (offset: number) => {
        if (mediaRef.current) {
            const newTime = Math.max(0, Math.min(duration, mediaRef.current.currentTime + offset));
            mediaRef.current.currentTime = newTime;
            setCurrentTime(newTime);
        }
    };

    const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newTime = Number(e.target.value);
        if (mediaRef.current) {
            mediaRef.current.currentTime = newTime;
            setCurrentTime(newTime);
        }
    };

    const handleTimeUpdate = () => {
        if (mediaRef.current) {
            setCurrentTime(mediaRef.current.currentTime);
        }
    };

    const handleLoadedMetadata = () => {
        if (mediaRef.current) {
            setDuration(mediaRef.current.duration);
            // Jump to start timecode
            mediaRef.current.currentTime = startTime;
        }
    };

    const handleCloseModal = () => {
        if (mediaRef.current) {
            mediaRef.current.pause();
        }
        setIsPlaying(false);
        onClose();
    };

    // Highlight query matches in transcript
    const highlightMatches = (text: string) => {
        if (!query) return text;
        const regex = new RegExp(`(${query.split(' ').join('|')})`, 'gi');
        return text.replace(regex, '<mark class="bg-yellow-300 dark:bg-yellow-600 px-0.5 rounded">$1</mark>');
    };

    if (!source) return null;

    const isVideo = source.sourceType === 'video';
    const streamUrl = getMediaStreamUrl(source.id, startTime);

    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={handleCloseModal}>
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" />
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
                            <DialogPanel className="w-full max-w-4xl transform rounded-2xl bg-light-secondary dark:bg-dark-secondary border border-light-200 dark:border-dark-200 shadow-xl transition-all overflow-hidden">
                                {/* Header */}
                                <div className="flex items-center justify-between p-4 border-b border-light-200 dark:border-dark-200">
                                    <DialogTitle className="flex items-center space-x-3">
                                        <div className={`p-2 rounded-lg ${isVideo ? 'bg-red-500/20 text-red-500' : 'bg-purple-500/20 text-purple-500'}`}>
                                            {isVideo ? <Video size={20} /> : <Volume2 size={20} />}
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-medium dark:text-white truncate max-w-md">
                                                {source.filename}
                                            </h3>
                                            <p className="text-xs text-black/50 dark:text-white/50">
                                                Startet bei {source.timecodeStart || '00:00'}
                                            </p>
                                        </div>
                                    </DialogTitle>
                                    <button
                                        onClick={handleCloseModal}
                                        className="p-2 rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition"
                                    >
                                        <X size={20} className="text-black/50 dark:text-white/50" />
                                    </button>
                                </div>

                                {/* Media Player */}
                                <div className="bg-black aspect-video flex items-center justify-center">
                                    {isVideo ? (
                                        <video
                                            ref={mediaRef as React.RefObject<HTMLVideoElement>}
                                            src={streamUrl}
                                            className="w-full h-full"
                                            onTimeUpdate={handleTimeUpdate}
                                            onLoadedMetadata={handleLoadedMetadata}
                                            onPlay={() => setIsPlaying(true)}
                                            onPause={() => setIsPlaying(false)}
                                            data-testid="media-preview-player"
                                        />
                                    ) : (
                                        <div className="flex flex-col items-center justify-center space-y-4 p-8">
                                            <div className="bg-purple-500/20 p-8 rounded-full">
                                                <Volume2 size={64} className="text-purple-400" />
                                            </div>
                                            <audio
                                                ref={mediaRef as React.RefObject<HTMLAudioElement>}
                                                src={streamUrl}
                                                onTimeUpdate={handleTimeUpdate}
                                                onLoadedMetadata={handleLoadedMetadata}
                                                onPlay={() => setIsPlaying(true)}
                                                onPause={() => setIsPlaying(false)}
                                                data-testid="media-preview-player"
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Controls */}
                                <div className="p-4 space-y-3">
                                    {/* Progress bar */}
                                    <div className="flex items-center space-x-3">
                                        <span className="text-xs font-mono text-black/70 dark:text-white/70 w-12">
                                            {formatTime(currentTime)}
                                        </span>
                                        <input
                                            type="range"
                                            min={0}
                                            max={duration || 100}
                                            value={currentTime}
                                            onChange={handleSliderChange}
                                            className="flex-1 h-2 bg-light-200 dark:bg-dark-200 rounded-lg appearance-none cursor-pointer accent-sky-500"
                                        />
                                        <span className="text-xs font-mono text-black/70 dark:text-white/70 w-12 text-right">
                                            {formatTime(duration)}
                                        </span>
                                    </div>

                                    {/* Playback buttons */}
                                    <div className="flex items-center justify-center space-x-4">
                                        <button
                                            onClick={() => handleSeek(-10)}
                                            className="p-3 rounded-full hover:bg-light-200 dark:hover:bg-dark-200 transition text-black/70 dark:text-white/70"
                                        >
                                            <SkipBack size={20} />
                                        </button>
                                        <button
                                            onClick={handlePlayPause}
                                            className="p-4 bg-sky-500 hover:bg-sky-600 rounded-full transition text-white"
                                        >
                                            {isPlaying ? <Pause size={24} /> : <Play size={24} />}
                                        </button>
                                        <button
                                            onClick={() => handleSeek(10)}
                                            className="p-3 rounded-full hover:bg-light-200 dark:hover:bg-dark-200 transition text-black/70 dark:text-white/70"
                                        >
                                            <SkipForward size={20} />
                                        </button>
                                    </div>
                                </div>

                                {/* Transcript */}
                                <div className="p-4 border-t border-light-200 dark:border-dark-200 max-h-48 overflow-y-auto">
                                    <h4 className="text-sm font-medium text-black/70 dark:text-white/70 mb-2">
                                        Transkript
                                    </h4>
                                    <p
                                        className="text-sm text-black/80 dark:text-white/80 leading-relaxed"
                                        dangerouslySetInnerHTML={{
                                            __html: highlightMatches(source.textSnippet),
                                        }}
                                    />
                                </div>
                            </DialogPanel>
                        </TransitionChild>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
};

export default MediaPlayerModal;
