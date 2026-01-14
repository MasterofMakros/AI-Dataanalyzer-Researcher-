/**
 * Local Media Preview Component
 * 
 * Sidebar component showing video/audio thumbnails from local Neural Vault sources.
 * Similar to SearchImages but for local sources with timecodes.
 */

'use client';

import { useState } from 'react';
import { Database, Play, Volume2 } from 'lucide-react';
import { LocalSource } from '@/lib/types';
import MediaPlayerModal from './MediaPlayerModal';

interface LocalMediaPreviewProps {
    localSources: LocalSource[];
    query: string;
}

const LocalMediaPreview = ({ localSources, query }: LocalMediaPreviewProps) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedSource, setSelectedSource] = useState<LocalSource | null>(null);

    // Filter to only video/audio sources
    const mediaSources = localSources.filter(
        (s) => s.sourceType === 'video' || s.sourceType === 'audio'
    );

    if (mediaSources.length === 0) {
        return null;
    }

    const handleSourceClick = (source: LocalSource) => {
        setSelectedSource(source);
        setIsModalOpen(true);
    };

    const getSourceIcon = (type: LocalSource['sourceType']) => {
        return type === 'video' ? (
            <Play size={12} className="text-white" />
        ) : (
            <Volume2 size={12} className="text-white" />
        );
    };

    const getSourceColor = (type: LocalSource['sourceType']) => {
        return type === 'video' ? 'bg-red-500' : 'bg-purple-500';
    };

    return (
        <>
            {/* Header */}
            <div className="flex items-center space-x-2 mb-2">
                <Database size={14} className="text-blue-400" />
                <span className="text-xs font-medium text-black/60 dark:text-white/60">
                    Lokale Medien ({mediaSources.length})
                </span>
            </div>

            {/* Media Grid */}
            <div className="grid grid-cols-2 gap-2">
                {mediaSources.slice(0, 3).map((source, i) => (
                    <button
                        key={source.id}
                        onClick={() => handleSourceClick(source)}
                        className="relative bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg overflow-hidden aspect-video group"
                    >
                        {/* Thumbnail or placeholder */}
                        <div className="absolute inset-0 bg-gradient-to-br from-dark-100 to-dark-200 flex items-center justify-center">
                            <div className={`${getSourceColor(source.sourceType)} p-3 rounded-full`}>
                                {getSourceIcon(source.sourceType)}
                            </div>
                        </div>

                        {/* Timecode badge */}
                        {source.timecodeStart && (
                            <div className="absolute bottom-1 left-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded font-mono">
                                {source.timecodeStart}
                            </div>
                        )}

                        {/* Play overlay */}
                        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/30">
                            <div className={`${getSourceColor(source.sourceType)} p-2 rounded-full`}>
                                <Play size={16} className="text-white" />
                            </div>
                        </div>

                        {/* Source type badge */}
                        <div className={`absolute top-1 right-1 ${getSourceColor(source.sourceType)} text-white text-[9px] px-1.5 py-0.5 rounded-md flex items-center space-x-1`}>
                            {getSourceIcon(source.sourceType)}
                            <span>{source.sourceType === 'video' ? 'Video' : 'Audio'}</span>
                        </div>
                    </button>
                ))}

                {/* View more button */}
                {mediaSources.length > 3 && (
                    <button
                        onClick={() => handleSourceClick(mediaSources[3])}
                        className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg flex flex-col items-center justify-center aspect-video"
                    >
                        <div className="flex -space-x-2 mb-1">
                            {mediaSources.slice(3, 6).map((source, i) => (
                                <div
                                    key={i}
                                    className={`w-6 h-6 ${getSourceColor(source.sourceType)} rounded-full flex items-center justify-center border-2 border-light-100 dark:border-dark-100`}
                                >
                                    {getSourceIcon(source.sourceType)}
                                </div>
                            ))}
                        </div>
                        <p className="text-xs text-black/50 dark:text-white/50">
                            +{mediaSources.length - 3} weitere
                        </p>
                    </button>
                )}
            </div>

            {/* Transcript snippets */}
            <div className="mt-2 space-y-1">
                {mediaSources.slice(0, 2).map((source) => (
                    <button
                        key={`text-${source.id}`}
                        onClick={() => handleSourceClick(source)}
                        className="w-full text-left p-2 bg-light-100/50 dark:bg-dark-100/50 rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition"
                    >
                        <div className="flex items-center space-x-2 mb-1">
                            <span className="text-[10px] font-mono text-blue-400">
                                {source.timecodeStart || '00:00'}
                            </span>
                            <span className="text-[10px] text-black/40 dark:text-white/40 truncate flex-1">
                                {source.filename}
                            </span>
                        </div>
                        <p className="text-xs text-black/70 dark:text-white/70 line-clamp-2">
                            &ldquo;{source.textSnippet}&rdquo;
                        </p>
                    </button>
                ))}
            </div>

            {/* Media Player Modal */}
            <MediaPlayerModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                source={selectedSource}
                query={query}
            />
        </>
    );
};

export default LocalMediaPreview;
