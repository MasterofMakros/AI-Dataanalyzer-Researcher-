'use client';

import { useState, useEffect } from 'react';
import { FileText, ExternalLink, ChevronRight, Loader2, X, Link2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface RelatedDocument {
  id: string;
  title: string;
  snippet: string;
  url?: string;
  filepath?: string;
  relation: 'mentions' | 'cites' | 'similar' | 'same_topic';
  relevanceScore: number;
  fileType?: string;
}

interface RelatedDocsPanelProps {
  documentId?: string;
  query?: string;
  sources?: Array<{
    title: string;
    url?: string;
    filepath?: string;
  }>;
  isOpen: boolean;
  onClose: () => void;
  onDocumentClick?: (doc: RelatedDocument) => void;
}

const relationLabels: Record<string, { label: string; color: string }> = {
  mentions: { label: 'Mentions', color: 'text-blue-500 bg-blue-500/10' },
  cites: { label: 'Cites', color: 'text-purple-500 bg-purple-500/10' },
  similar: { label: 'Similar', color: 'text-emerald-500 bg-emerald-500/10' },
  same_topic: { label: 'Same Topic', color: 'text-amber-500 bg-amber-500/10' },
};

const RelatedDocsPanel = ({
  documentId,
  query,
  sources,
  isOpen,
  onClose,
  onDocumentClick,
}: RelatedDocsPanelProps) => {
  const [relatedDocs, setRelatedDocs] = useState<RelatedDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    const fetchRelatedDocs = async () => {
      setLoading(true);
      setError(null);

      try {
        // TODO: Integrate with actual backend API when available
        // For now, simulate with mock data based on sources
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Generate mock related documents based on available sources
        if (sources && sources.length > 0) {
          const mockDocs: RelatedDocument[] = sources.slice(0, 5).map((source, index) => ({
            id: `related-${index}`,
            title: source.title || `Related Document ${index + 1}`,
            snippet: `This document is related to your current search and contains relevant information...`,
            url: source.url,
            filepath: source.filepath,
            relation: (['mentions', 'cites', 'similar', 'same_topic'] as const)[index % 4],
            relevanceScore: Math.round((100 - index * 10) * 100) / 100,
            fileType: source.filepath?.split('.').pop()?.toUpperCase() || 'WEB',
          }));
          setRelatedDocs(mockDocs);
        } else {
          setRelatedDocs([]);
        }
      } catch (err) {
        setError('Failed to load related documents');
        console.error('Error fetching related documents:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchRelatedDocs();
  }, [isOpen, documentId, query, sources]);

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-light-primary dark:bg-dark-primary border-l border-light-200 dark:border-dark-200 shadow-lg z-40 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-light-200 dark:border-dark-200">
        <div className="flex items-center gap-2">
          <Link2 className="w-5 h-5 text-sky-500" />
          <h2 className="text-lg font-medium text-black dark:text-white">
            Related Documents
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition-colors"
        >
          <X className="w-5 h-5 text-black/60 dark:text-white/60" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="w-8 h-8 text-sky-500 animate-spin" />
            <p className="mt-2 text-sm text-black/60 dark:text-white/60">
              Finding related documents...
            </p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-8">
            <p className="text-sm text-red-500">{error}</p>
          </div>
        ) : relatedDocs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8">
            <FileText className="w-12 h-12 text-black/20 dark:text-white/20" />
            <p className="mt-2 text-sm text-black/60 dark:text-white/60 text-center">
              No related documents found
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {relatedDocs.map((doc) => {
              const relationInfo = relationLabels[doc.relation] || relationLabels.similar;

              return (
                <button
                  key={doc.id}
                  onClick={() => onDocumentClick?.(doc)}
                  className="w-full text-left p-3 rounded-lg border border-light-200 dark:border-dark-200 hover:bg-light-secondary dark:hover:bg-dark-secondary transition-colors group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={cn(
                            'text-xs px-1.5 py-0.5 rounded',
                            relationInfo.color
                          )}
                        >
                          {relationInfo.label}
                        </span>
                        {doc.fileType && (
                          <span className="text-xs text-black/40 dark:text-white/40">
                            {doc.fileType}
                          </span>
                        )}
                      </div>
                      <h3 className="text-sm font-medium text-black dark:text-white line-clamp-2 group-hover:text-sky-500 transition-colors">
                        {doc.title}
                      </h3>
                      <p className="text-xs text-black/60 dark:text-white/60 line-clamp-2 mt-1">
                        {doc.snippet}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-black/30 dark:text-white/30 group-hover:text-sky-500 transition-colors shrink-0 mt-1" />
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-black/40 dark:text-white/40">
                      Relevance: {doc.relevanceScore}%
                    </span>
                    {doc.url && (
                      <ExternalLink className="w-3 h-3 text-black/40 dark:text-white/40" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-light-200 dark:border-dark-200 bg-light-secondary/50 dark:bg-dark-secondary/50">
        <p className="text-xs text-black/50 dark:text-white/50 text-center">
          Based on Knowledge Graph connections
        </p>
      </div>
    </div>
  );
};

export default RelatedDocsPanel;
