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
  onClick?: () => void;
}

const PdfPreviewCard = ({
  title,
  href,
  snippet,
  pageNumber,
  totalPages,
  sourceLabel,
  index,
  onClick,
}: PdfPreviewCardProps) => {
  const pageLabel = pageNumber
    ? `${pageNumber}${totalPages ? `/${totalPages}` : ''}`
    : undefined;

  return (
    <PreviewCard href={href} onClick={onClick}>
      <div className="flex items-center justify-between text-xs text-black/50 dark:text-white/50">
        <div className="flex items-center space-x-2">
          <div className="bg-orange-500/10 text-orange-500 p-1 rounded-md">
            <FileText size={12} />
          </div>
          <span className="uppercase tracking-wide">PDF</span>
        </div>
        <span>#{index + 1}</span>
      </div>

      <p className="dark:text-white text-xs font-medium overflow-hidden whitespace-nowrap text-ellipsis">
        {title}
      </p>

      <div className="flex items-center justify-between text-[10px] text-black/50 dark:text-white/50">
        <span>{pageLabel ? `Page ${pageLabel}` : 'Page unknown'}</span>
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

export default PdfPreviewCard;
