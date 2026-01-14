/**
 * PDF Preview Card Component
 *
 * Displays PDF/doc sources with page number and snippet preview.
 */

'use client';

import { FileText, BookOpen, ExternalLink } from 'lucide-react';
import { LocalSource } from '@/lib/types';

interface PdfPreviewCardProps {
    source: LocalSource;
    index: number;
    onClick?: () => void;
}

const PdfPreviewCard = ({ source, index, onClick }: PdfPreviewCardProps) => {
    const handleClick = () => {
        if (onClick) onClick();
    };

    const extension = source.filename.split('.').pop()?.toLowerCase() || '';
    const isPdf = extension === 'pdf';

    return (
        <div
            className="bg-light-100 hover:bg-light-200 dark:bg-dark-100 dark:hover:bg-dark-200 transition duration-200 rounded-lg p-3 flex flex-col space-y-2 cursor-pointer"
            onClick={handleClick}
        >
            <div className="flex items-center space-x-2">
                <div className={`${isPdf ? 'bg-red-500/20 text-red-500' : 'bg-blue-500/20 text-blue-500'} p-1.5 rounded-lg`}>
                    <FileText size={14} />
                </div>
                <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis flex-1">
                    {source.filename}
                </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-[11px] text-black/50 dark:text-white/50">
                {source.pageNumber && (
                    <span className="bg-blue-500/10 text-blue-400 px-2 py-1 rounded-md flex items-center space-x-1">
                        <BookOpen size={10} />
                        <span>
                            Seite {source.pageNumber}
                            {source.totalPages ? ` / ${source.totalPages}` : ''}
                        </span>
                    </span>
                )}
                {source.confidence ? (
                    <span className="bg-black/5 dark:bg-white/10 px-2 py-1 rounded-md">
                        {Math.round(source.confidence)}% Match
                    </span>
                ) : null}
            </div>

            {source.thumbnailUrl && (
                <div className="relative bg-black/10 dark:bg-white/10 rounded-md h-20 overflow-hidden">
                    <img
                        src={source.thumbnailUrl}
                        alt={source.filename}
                        className="w-full h-full object-cover"
                    />
                </div>
            )}

            <div className="bg-black/5 dark:bg-white/5 rounded-md p-2">
                <p className="text-xs text-black/70 dark:text-white/70 line-clamp-3 italic">
                    &ldquo;{source.textSnippet}&rdquo;
                </p>
            </div>

            <div className="flex items-center justify-between text-xs text-black/40 dark:text-white/40">
                <div className="flex items-center space-x-1">
                    <ExternalLink size={10} />
                    <span>PDF öffnen</span>
                </div>
                <span>#{index + 1}</span>
            </div>
        </div>
    );
'use client';

import { FileText } from 'lucide-react';
import PreviewCard from './PreviewCard';

interface PdfPreviewCardProps {
  title: string;
  href?: string;
  snippet?: string;
  pageNumber?: number;
  totalPages?: number;
  sourceLabel?: string;
  index: number;
}

const PdfPreviewCard = ({
  title,
  href,
  snippet,
  pageNumber,
  totalPages,
  sourceLabel,
  index,
}: PdfPreviewCardProps) => {
  return (
    <PreviewCard href={href}>
      <div className="flex items-center justify-between text-xs text-black/50 dark:text-white/50">
        <div className="flex items-center space-x-2">
          <div className="bg-red-500/10 text-red-500 p-1 rounded-md">
            <FileText size={12} />
          </div>
          <span className="uppercase tracking-wide">PDF</span>
        </div>
        <span>#{index + 1}</span>
      </div>

      <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis">
        {title}
      </p>

      <div className="rounded-md border border-dashed border-black/10 dark:border-white/10 bg-white/60 dark:bg-black/20 p-3">
        <div className="flex items-center justify-between text-xs text-black/60 dark:text-white/60">
          <span>Seitenvorschau</span>
          {pageNumber ? (
            <span className="font-mono">
              Seite {pageNumber}
              {totalPages ? ` / ${totalPages}` : ''}
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

      {snippet && (
        <p className="text-xs text-black/70 dark:text-white/70 line-clamp-3 italic">
          &ldquo;{snippet}&rdquo;
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

export default PdfPreviewCard;
