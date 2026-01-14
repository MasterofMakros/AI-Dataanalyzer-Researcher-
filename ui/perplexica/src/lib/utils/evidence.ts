import { Evidence } from '@/lib/types';

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
