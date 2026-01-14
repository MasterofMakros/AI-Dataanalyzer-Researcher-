import { Chunk, Evidence } from '@/lib/types';

const serializeEvidence = (evidence: Evidence) =>
  JSON.stringify({
    page: evidence.page,
    bbox: evidence.bbox,
    timecodeStart: evidence.timecodeStart,
    timecodeEnd: evidence.timecodeEnd,
    timestamp: evidence.timestamp,
  });

export const mergeEvidence = (
  existing: Evidence[] | undefined = [],
  incoming: Evidence[] | undefined = [],
): Evidence[] => {
  const merged = [...(existing || []), ...(incoming || [])].filter(Boolean);
  const seen = new Set<string>();

  return merged.filter((item) => {
    const key = serializeEvidence(item);
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
};

const getBBoxFromMetadata = (
  bbox: unknown,
): Evidence['bbox'] | undefined => {
  if (Array.isArray(bbox) && bbox.length === 4) {
    const parsed = bbox.map((value) => Number(value));
    if (parsed.every((value) => !Number.isNaN(value))) {
      return parsed as Evidence['bbox'];
    }
  }

  return undefined;
};

const buildEvidenceFromMetadata = (
  metadata: Record<string, any> | undefined,
): Evidence[] => {
  if (!metadata) {
    return [];
  }

  const evidence: Evidence = {};

  if (typeof metadata.page === 'number') {
    evidence.page = metadata.page;
  }

  const bbox = getBBoxFromMetadata(metadata.bbox);
  if (bbox) {
    evidence.bbox = bbox;
  }

  if (typeof metadata.timecodeStart === 'string') {
    evidence.timecodeStart = metadata.timecodeStart;
  }

  if (typeof metadata.timecodeEnd === 'string') {
    evidence.timecodeEnd = metadata.timecodeEnd;
  }

  if (typeof metadata.timestamp === 'number') {
    evidence.timestamp = metadata.timestamp;
  }

  return Object.keys(evidence).length > 0 ? [evidence] : [];
};

export const normalizeChunkEvidence = (chunk: Chunk): Chunk => {
  const metadataEvidence = buildEvidenceFromMetadata(chunk.metadata);
  const evidence = mergeEvidence(chunk.evidence ?? [], metadataEvidence);

  return {
    ...chunk,
    evidence,
  };
};

export const normalizeChunksEvidence = (chunks: Chunk[]): Chunk[] =>
  chunks.map(normalizeChunkEvidence);
