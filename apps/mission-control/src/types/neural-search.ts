// Neural Search Types

export type SearchStep = 'analyzing' | 'searching' | 'reading' | 'synthesizing' | 'complete';

export type SourceType = 'pdf' | 'audio' | 'image' | 'email' | 'video' | 'text';

export interface SearchProgress {
  step: SearchStep;
  progress: number;
  keywords?: string[];
  documentsFound?: number;
  documentsTotal?: number;
  currentSource?: string;
  sourcesRead?: number;
  sourcesTotal?: number;
}

export interface Source {
  id: string;
  type: SourceType;
  filename: string;
  path: string;
  confidence: number;
  excerpt: string;
  highlightedText?: string;
  page?: number;
  line?: string;
  timestamp?: string;  // For audio/video
  duration?: string;   // For audio/video
  speakers?: string[]; // For audio with diarization
  transcript?: TranscriptLine[];
  extractedVia: string; // 'Docling', 'Surya', 'WhisperX', 'Tika'
  boundingBox?: BoundingBox;
}

export interface TranscriptLine {
  timestamp: string;
  speaker: string;
  text: string;
  isHighlighted?: boolean;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Citation {
  index: number;
  sourceId: string;
  text: string;
}

export interface SearchResponse {
  id: string;
  query: string;
  answer: string;
  citations: Citation[];
  sources: Source[];
  timestamp: Date;
  processingTimeMs: number;
}

export interface FollowUpQuestion {
  id: string;
  icon: string;
  question: string;
}

export interface PIIItem {
  type: 'email' | 'phone' | 'iban' | 'address' | 'name' | 'date';
  original: string;
  masked: string;
  icon: string;
}

export interface PipelineStatus {
  gpuStatus: 'online' | 'offline' | 'busy';
  gpuModel: string;
  vramUsage: number;
  workersActive: number;
  workersTotal: number;
  queueDepth: number;
  indexedDocuments: number;
  lastSync: Date;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: Date;
  sourcesCount: number;
}

// Timeline types
export interface TimelineEvent {
  id: string;
  date: Date;
  icon: string;
  title: string;
  description: string;
  sourceId: string;
  sourceFilename: string;
}

// Entity Graph types
export interface GraphNode {
  id: string;
  label: string;
  type: 'entity' | 'amount' | 'date' | 'ticket' | 'location';
  value?: string;
}

export interface GraphEdge {
  from: string;
  to: string;
  label?: string;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
