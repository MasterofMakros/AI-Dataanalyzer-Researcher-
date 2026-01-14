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
