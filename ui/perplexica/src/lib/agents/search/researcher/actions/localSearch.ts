/**
 * Local Search Action - Neural Vault Integration
 * 
 * Searches local documents indexed in Neural Vault via Qdrant.
 * Returns sources with timecodes for audio/video, page numbers for documents.
 */

import { z } from 'zod';
import { ResearchAction, ActionOutput, AdditionalConfig, SearchSources } from '../../types';
import { searchNeuralVault, LocalSource } from '@/lib/neuralVault';
import { Chunk, Evidence } from '@/lib/types';

const localSearchSchema = z.object({
    queries: z
        .array(z.string())
        .describe('List of search queries to run on local documents'),
    sourceTypes: z
        .array(z.enum(['document', 'audio', 'video', 'image']))
        .optional()
        .describe('Filter by source type (document, audio, video, image)'),
});

type LocalSearchParams = z.infer<typeof localSearchSchema>;

const localSearchAction: ResearchAction<typeof localSearchSchema> = {
    name: 'local_search',

    schema: localSearchSchema,

    enabled: (config) => {
        // Enable when 'local' source is selected
        return config.sources.includes('local' as SearchSources);
    },

    getDescription: ({ mode }) => {
        return `Search through locally indexed documents from Neural Vault.
This includes PDFs, Word documents, images (with OCR), audio/video transcriptions.
Results include:
- For audio/video: Timecodes to jump to specific positions
- For documents: Page numbers
- For images: OCR text and thumbnails

Use this when the user wants to search their own files and documents.`;
    },

    getToolDescription: ({ mode }) => {
        return 'Search local documents indexed in Neural Vault. Returns sources with timecodes, page numbers, and OCR text.';
    },

    execute: async (
        params: LocalSearchParams,
        config: AdditionalConfig & { researchBlockId: string; fileIds: string[] },
    ): Promise<ActionOutput> => {
        const { queries, sourceTypes } = params;

        // Determine limit based on optimization mode
        const mode = config.mode || 'balanced';
        const limitByMode: Record<string, number> = {
            speed: 3,      // Fast: minimal sources
            balanced: 8,   // Default: moderate sources
            quality: 15,   // Thorough: maximum sources
        };
        const limit = limitByMode[mode] || 8;

        // Emit searching status
        const block = config.session.getBlock(config.researchBlockId);
        if (block && block.type === 'research') {
            block.data.subSteps.push({
                id: crypto.randomUUID(),
                type: 'searching',
                searching: queries.map(q => `[Local] ${q}`),
            });
            config.session.updateBlock(config.researchBlockId, [
                {
                    op: 'replace',
                    path: '/data/subSteps',
                    value: block.data.subSteps,
                },
            ]);
        }

        // Execute searches with mode-based limit
        const allSources: LocalSource[] = [];

        for (const query of queries) {
            const result = await searchNeuralVault(query, {
                limit: limit,
                sourceTypes: sourceTypes,
            });
            allSources.push(...result.sources);
        }

        // Deduplicate by ID
        const uniqueSources = Array.from(
            new Map(allSources.map(s => [s.id, s])).values()
        );

        // Convert to Chunk format for compatibility with existing system
        const chunks: Chunk[] = uniqueSources.map(source => {
            // Build metadata with source-specific info
            const metadata: Record<string, any> = {
                title: source.filename,
                url: source.filePath,
                sourceType: source.sourceType,
                confidence: source.confidence,
            };

            const evidence: Evidence = {};

            // Add timecodes for audio/video
            if (source.timecodeStart) {
                metadata.timecodeStart = source.timecodeStart;
                metadata.timecodeEnd = source.timecodeEnd;
                evidence.timecodeStart = source.timecodeStart;
                evidence.timecodeEnd = source.timecodeEnd;
            }

            // Add page info for documents
            if (source.pageNumber) {
                metadata.page = source.pageNumber;
                metadata.totalPages = source.totalPages;
                evidence.page = source.pageNumber;
                evidence.totalPages = source.totalPages;
            }

            if (source.timestampStart !== undefined) {
                evidence.timestampStart = source.timestampStart;
                evidence.timestampEnd = source.timestampEnd;
            }

            if (source.bbox) {
                evidence.bbox = source.bbox;
            }

            // Add thumbnail for images
            if (source.thumbnailUrl) {
                metadata.thumbnailUrl = source.thumbnailUrl;
                metadata.ocrText = source.ocrText;
            }

            return {
                content: source.textSnippet,
                metadata,
                evidence: Object.keys(evidence).length > 0 ? [evidence] : undefined,
            };
        });

        // Emit reading status
        if (block && block.type === 'research') {
            block.data.subSteps.push({
                id: crypto.randomUUID(),
                type: 'reading',
                reading: chunks.slice(0, 5),
            });
            config.session.updateBlock(config.researchBlockId, [
                {
                    op: 'replace',
                    path: '/data/subSteps',
                    value: block.data.subSteps,
                },
            ]);
        }

        return {
            type: 'search_results',
            results: chunks,
        };
    },
};

export default localSearchAction;
