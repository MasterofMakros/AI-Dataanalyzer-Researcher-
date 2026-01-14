/**
 * Neural Vault Local Search Client
 * 
 * Searches local documents indexed in Neural Vault via Qdrant.
 * Provides source previews with timecodes for audio/video,
 * page numbers for documents, and OCR text for images.
 */

// Neural Vault API URL (set via environment or default)
const getNeuralVaultURL = (): string => {
  return process.env.NEURAL_VAULT_API_URL || 'http://conductor-api:8010';
};

export interface LocalSourceOptions {
  limit?: number;
  sourceTypes?: ('document' | 'audio' | 'video' | 'image')[];
  includeWeb?: boolean;  // For hybrid mode
}

export interface LocalSource {
  id: string;
  filename: string;
  sourceType: 'document' | 'audio' | 'video' | 'image';
  textSnippet: string;
  confidence: number;
  // Audio/Video timecodes
  timecodeStart?: string;
  timecodeEnd?: string;
  // Document page info
  pageNumber?: number;
  totalPages?: number;
  // Image OCR
  thumbnailUrl?: string;
  ocrText?: string;
  // Metadata
  filePath: string;
  folder?: string;
  fileExtension?: string;
  fileCreated?: string;
  fileModified?: string;
  indexedAt?: string;
  tags?: string[];
}

export interface LocalSearchResult {
  query: string;
  sources: LocalSource[];
  totalResults: number;
  processingTimeMs: number;
}

/**
 * Search local documents in Neural Vault
 */
export const searchNeuralVault = async (
  query: string,
  opts?: LocalSourceOptions,
): Promise<LocalSearchResult> => {
  const apiUrl = getNeuralVaultURL();
  
  try {
    const response = await fetch(`${apiUrl}/rag/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        limit: opts?.limit || 10,
        source_types: opts?.sourceTypes,
        include_web: opts?.includeWeb || false,
      }),
    });

    if (!response.ok) {
      console.error('Neural Vault search failed:', response.statusText);
      return {
        query,
        sources: [],
        totalResults: 0,
        processingTimeMs: 0,
      };
    }

    const data = await response.json();
    
    // Transform snake_case to camelCase
  const sources: LocalSource[] = (data.sources || []).map((s: any) => ({
      id: s.id,
      filename: s.filename,
      sourceType: s.source_type,
      textSnippet: s.text_snippet,
      confidence: s.confidence,
      timecodeStart: s.timecode_start,
      timecodeEnd: s.timecode_end,
      pageNumber: s.page_number,
      totalPages: s.total_pages,
      thumbnailUrl: s.thumbnail_url,
      ocrText: s.ocr_text,
      filePath: s.file_path,
      folder: s.folder,
      fileExtension: s.file_extension,
      fileCreated: s.file_created,
      fileModified: s.file_modified,
      indexedAt: s.indexed_at,
      tags: s.tags,
    }));

    return {
      query: data.query,
      sources,
      totalResults: data.total_results,
      processingTimeMs: data.processing_time_ms,
    };
  } catch (error) {
    console.error('Neural Vault search error:', error);
    return {
      query,
      sources: [],
      totalResults: 0,
      processingTimeMs: 0,
    };
  }
};

/**
 * Get detailed source information including full timecodes
 */
export const getSourceDetails = async (sourceId: string) => {
  const apiUrl = getNeuralVaultURL();
  
  try {
    const response = await fetch(`${apiUrl}/sources/${sourceId}`);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to get source details:', error);
    return null;
  }
};

/**
 * Get media stream URL with optional start position
 */
export const getMediaStreamUrl = (sourceId: string, startSeconds?: number): string => {
  const apiUrl = getNeuralVaultURL();
  const url = new URL(`${apiUrl}/sources/${sourceId}/stream`);
  if (startSeconds !== undefined) {
    url.searchParams.append('start', startSeconds.toString());
  }
  return url.toString();
};

/**
 * Get thumbnail URL for image sources
 */
export const getThumbnailUrl = (sourceId: string): string => {
  const apiUrl = getNeuralVaultURL();
  return `${apiUrl}/sources/${sourceId}/thumbnail`;
};
