/**
 * Document Source Card Component
 * 
 * Displays a document source with page number and text preview.
 */

'use client';

import { ExternalLink } from 'lucide-react';
import { LocalSource } from '@/lib/types';
import FormatIcon from './FormatIcon';

interface DocumentSourceCardProps {
    source: LocalSource;
    index: number;
    onClick?: () => void;
    testId?: string;
}

const DocumentSourceCard = ({ source, index, onClick, testId }: DocumentSourceCardProps) => {
    const handleClick = () => {
        if (onClick) onClick();
        console.log(`Open document ${source.filename} at page ${source.pageNumber}`);
    };

    // Get file extension for icon styling
    const extension = source.filename.split('.').pop()?.toLowerCase() || '';
    const isPDF = extension === 'pdf';
    const isSpreadsheet = ['xlsx', 'xls', 'csv'].includes(extension);

    const iconColor = isPDF
        ? 'bg-red-500/20 text-red-500'
        : isSpreadsheet
            ? 'bg-green-500/20 text-green-500'
            : 'bg-blue-500/20 text-blue-500';

    return (
        <div
            className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 cursor-pointer"
            onClick={handleClick}
            data-testid={testId}
        >
            {/* Header */}
            <div className="flex items-center space-x-2">
                <div className={`${iconColor} p-1.5 rounded-lg flex items-center justify-center`}>
                    <FormatIcon format={extension || 'file'} size={14} />
                </div>
                <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis flex-1">
                    {source.filename}
                </p>
            </div>

            {/* Page preview for PDFs */}
            {isPDF && (
                <div className="rounded-md border border-dashed border-black/10 dark:border-white/10 bg-white/60 dark:bg-black/20 p-2">
                    <div className="flex items-center justify-between text-xs text-black/50 dark:text-white/50">
                        <span>Seitenvorschau</span>
                        {source.pageNumber ? (
                            <span className="font-mono">
                                Seite {source.pageNumber}
                                {source.totalPages ? ` / ${source.totalPages}` : ''}
                            </span>
                        ) : (
                            <span className="font-mono">PDF</span>
                        )}
                    </div>
                    <div className="mt-2 space-y-1">
                        {[1, 2, 3].map((line) => (
                            <div
                                key={line}
                                className="h-1 rounded-full bg-black/10 dark:bg-white/10"
                                style={{ width: `${90 - line * 12}%` }}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Page indicator */}
            {source.pageNumber && (
                <div className="flex items-center space-x-2">
                    <span className="bg-blue-500/10 text-blue-400 text-xs px-2 py-1 rounded-md">
                        Seite {source.pageNumber}
                        {source.totalPages && (
                            <span className="text-blue-300"> / {source.totalPages}</span>
                        )}
                    </span>
                </div>
            )}

            {/* Text snippet with highlight effect */}
            <div className="bg-black/5 dark:bg-white/5 rounded-md p-2">
                <p className="text-xs text-black/70 dark:text-white/70 line-clamp-3 italic">
                    &ldquo;{source.textSnippet}&rdquo;
                </p>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between text-xs text-black/40 dark:text-white/40">
                <div className="flex items-center space-x-1">
                    <ExternalLink size={10} />
                    <span>Dokument öffnen</span>
                </div>
                <span>#{index + 1}</span>
            </div>
        </div>
    );
};

export default DocumentSourceCard;
