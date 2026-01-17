import { ToolCall } from './models/types';

export type SystemMessage = {
  role: 'system';
  content: string;
};

export type AssistantMessage = {
  role: 'assistant';
  content: string;
  tool_calls?: ToolCall[];
};

export type UserMessage = {
  role: 'user';
  content: string;
};

export type ToolMessage = {
  role: 'tool';
  id: string;
  name: string;
  content: string;
};

export type ChatTurnMessage = UserMessage | AssistantMessage;

export type Message =
  | UserMessage
  | AssistantMessage
  | SystemMessage
  | ToolMessage;

export type Evidence = {
  page?: number;
  totalPages?: number;
  bbox?: [number, number, number, number];
  timecodeStart?: string;
  timecodeEnd?: string;
  timestamp?: number;
  timestampStart?: number;
  timestampEnd?: number;
};

export type Chunk = {
  content: string;
  metadata: Record<string, any>;
  evidence?: Evidence[];
};

export type Claim = {
  id: string;
  text: string;
  evidenceIds: number[];
  verified: boolean;
};

export type TextBlock = {
  id: string;
  type: 'text';
  data: string;
};

export type ClaimEvidence = {
  id: string;
  index: number;
  title?: string;
  url?: string;
};

export type ClaimItem = {
  id: string;
  text: string;
  evidence: ClaimEvidence[];
  verified: boolean;
};

export type SourceBlock = {
  id: string;
  type: 'source';
  data: Chunk[];
};

export type SuggestionBlock = {
  id: string;
  type: 'suggestion';
  data: string[];
};

export type ClaimBlock = {
  id: string;
  type: 'claim';
  data: Claim[];
};

export type WidgetBlock = {
  id: string;
  type: 'widget';
  data: {
    widgetType: string;
    params: Record<string, any>;
  };
};

export type ReasoningResearchBlock = {
  id: string;
  type: 'reasoning';
  reasoning: string;
  durationMs?: number;
};

export type SearchingResearchBlock = {
  id: string;
  type: 'searching';
  searching: string[];
  durationMs?: number;
};

export type SearchResultsResearchBlock = {
  id: string;
  type: 'search_results';
  reading: Chunk[];
};

export type ReadingResearchBlock = {
  id: string;
  type: 'reading';
  reading: Chunk[];
  durationMs?: number;
};

export type UploadSearchingResearchBlock = {
  id: string;
  type: 'upload_searching';
  queries: string[];
  durationMs?: number;
};

export type UploadSearchResultsResearchBlock = {
  id: string;
  type: 'upload_search_results';
  results: Chunk[];
};

export type SynthesisResearchBlock = {
  id: string;
  type: 'synthesis';
};

export type ResearchPhase = 'analysis' | 'search' | 'reading' | 'synthesis';

export type ResearchBlockSubStep =
  | ReasoningResearchBlock
  | SearchingResearchBlock
  | SearchResultsResearchBlock
  | ReadingResearchBlock
  | UploadSearchingResearchBlock
  | UploadSearchResultsResearchBlock
  | SynthesisResearchBlock;

export type ResearchBlock = {
  id: string;
  type: 'research';
  data: {
    phase?: ResearchPhase;
    subSteps: ResearchBlockSubStep[];
  };
};

export type Block =
  | TextBlock
  | SourceBlock
  | ClaimBlock
  | SuggestionBlock
  | WidgetBlock
  | ResearchBlock;

// =============================================================================
// NEURAL VAULT LOCAL SOURCE TYPES
// =============================================================================

export type LocalSourceType = 'document' | 'audio' | 'video' | 'image';

export type LocalSource = {
  id: string;
  filename: string;
  sourceType: LocalSourceType;
  textSnippet: string;
  confidence: number;
  evidenceId?: number;
  // Audio/Video timecodes (format: "HH:MM:SS" or "MM:SS")
  timecodeStart?: string;
  timecodeEnd?: string;
  timestampStart?: number;
  timestampEnd?: number;
  // Document page info
  pageNumber?: number;
  totalPages?: number;
  bbox?: [number, number, number, number];
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
};

export type LocalSourceBlock = {
  id: string;
  type: 'local_source';
  data: LocalSource[];
};

export type HybridSearchResult = {
  webSources: Chunk[];
  localSources: LocalSource[];
  combinedAnswer?: string;
};
