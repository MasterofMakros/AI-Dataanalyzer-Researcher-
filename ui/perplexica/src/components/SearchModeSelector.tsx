import React, { useEffect, useState } from 'react';
import {
    Globe,
    BookOpen,
    Youtube,
    PenTool,
    LayoutTemplate,
    Library,
    Zap,
    Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useChat } from '@/lib/hooks/useChat';

interface SearchModeSelectorProps {
    onModeChange?: (mode: string) => void;
}

const focusModes = [
    { id: 'webSearch', label: 'Web', icon: Globe, description: 'Search the entire internet' },
    { id: 'academicSearch', label: 'Academic', icon: BookOpen, description: 'Published papers & research' },
    { id: 'writingAssistant', label: 'Writing', icon: PenTool, description: 'Generate & refine content' },
    { id: 'youtubeSearch', label: 'Video', icon: Youtube, description: 'Search video transcripts' },
    { id: 'redditSearch', label: 'Social', icon: LayoutTemplate, description: 'Discussions & forums' },
    // { id: 'local', label: 'Neural Vault', icon: Library, description: 'Local 10TB+ knowledge base' }, // Future integration
];

const SearchModeSelector: React.FC<SearchModeSelectorProps> = ({ onModeChange }) => {
    const { focusMode, setFocusMode } = useChat();
    const [optimizationMode, setOptimizationMode] = useState<'speed' | 'quality'>('speed');

    // Sync internal optimization state to localStorage or Context (Mocked for UI)
    const toggleOptimization = (mode: 'speed' | 'quality') => {
        setOptimizationMode(mode);
        // In future: updateConfig({ optimization: mode });
    };

    return (
        <div className="w-full max-w-3xl flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* Focus Mode Selection (Cards) */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {focusModes.map((mode) => {
                    const Icon = mode.icon;
                    const isActive = focusMode === mode.id;

                    return (
                        <button
                            key={mode.id}
                            onClick={() => setFocusMode(mode.id)}
                            className={cn(
                                'flex flex-col items-center justify-center p-3 gap-2 rounded-xl border transition-all duration-200 group',
                                isActive
                                    ? 'bg-light-secondary dark:bg-dark-secondary border-accent-blue shadow-sm'
                                    : 'bg-transparent border-transparent hover:bg-light-secondary/50 dark:hover:bg-dark-secondary/50'
                            )}
                        >
                            <div
                                className={cn(
                                    'p-2 rounded-full transition-colors',
                                    isActive
                                        ? 'bg-accent-blue/10 text-accent-blue'
                                        : 'text-black/50 dark:text-white/50 group-hover:text-black/70 dark:group-hover:text-white/70'
                                )}
                            >
                                <Icon size={20} />
                            </div>
                            <span
                                className={cn(
                                    'text-xs font-medium',
                                    isActive
                                        ? 'text-black dark:text-white'
                                        : 'text-black/50 dark:text-white/50'
                                )}
                            >
                                {mode.label}
                            </span>
                        </button>
                    );
                })}
            </div>

            {/* Optimization Toggle (Speed vs Quality) */}
            <div className="flex flex-row items-center justify-center gap-4 pt-2">
                <div className="flex bg-light-secondary dark:bg-dark-secondary p-1 rounded-full border border-light-200 dark:border-dark-200">
                    <button
                        onClick={() => toggleOptimization('speed')}
                        className={cn(
                            'flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium transition-all',
                            optimizationMode === 'speed'
                                ? 'bg-white dark:bg-dark-primary text-black dark:text-white shadow-sm'
                                : 'text-black/50 dark:text-white/50 hover:text-black/70 dark:hover:text-white/70'
                        )}
                    >
                        <Zap size={14} className={optimizationMode === 'speed' ? 'text-amber-400' : ''} />
                        Speed
                    </button>
                    <button
                        onClick={() => toggleOptimization('quality')}
                        className={cn(
                            'flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium transition-all',
                            optimizationMode === 'quality'
                                ? 'bg-white dark:bg-dark-primary text-black dark:text-white shadow-sm'
                                : 'text-black/50 dark:text-white/50 hover:text-black/70 dark:hover:text-white/70'
                        )}
                    >
                        <Sparkles size={14} className={optimizationMode === 'quality' ? 'text-accent-blue' : ''} />
                        Quality
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SearchModeSelector;
