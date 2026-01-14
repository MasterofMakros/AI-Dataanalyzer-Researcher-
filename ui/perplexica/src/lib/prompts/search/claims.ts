import { Chunk } from '@/lib/types';

const sanitizeSnippet = (snippet: string) =>
  snippet.replace(/\s+/g, ' ').trim().slice(0, 280);

export const getClaimsPrompt = (sources: Chunk[]) => {
  const sourcesList = sources
    .map((source, index) => {
      const title = source.metadata?.title ?? 'Untitled';
      const url = source.metadata?.url ?? '';
      const snippet = sanitizeSnippet(source.content || '');
      return `[${index + 1}] ${title} | ${url} | ${snippet}`;
    })
    .join('\n');

  return `You are an assistant that extracts factual claims from an answer and maps each claim to the provided evidence sources.

Return JSON that matches this schema:
{
  "claims": [
    {
      "text": "short, factual claim from the answer",
      "evidenceIds": [1, 2],
      "verified": true
    }
  ]
}

Rules:
- Extract only claims that appear in the answer verbatim or as clear paraphrases.
- Use evidenceIds that reference the numbered sources below.
- If a claim is not supported by any source, use an empty evidenceIds array and set verified to false.
- Keep each claim concise (one sentence) and limit the list to 8 claims.

Evidence sources:
${sourcesList || 'No sources provided.'}`;
};
