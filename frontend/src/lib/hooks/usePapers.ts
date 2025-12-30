import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api/client';
import { getPaperDetail } from '@/lib/api/papers';
import { RecommendationItemSchema } from '@/lib/utils/validators';

const CitationNetworkSchema = z.object({
  papers: z.array(
    z.object({
      paper_id: z.string(),
      title: z.string(),
      year: z.number().nullable(),
      citations: z.number(),
      impact_score: z.number().nullable(),
      community: z.number().nullable(),
      x: z.number().nullable(),
      y: z.number().nullable(),
    }),
  ),
  citations: z.array(
    z.object({
      source: z.string(),
      target: z.string(),
    }),
  ),
});

export type CitationNetwork = z.infer<typeof CitationNetworkSchema>;

export function usePaperDetail(paperId: string) {
  return useQuery({
    queryKey: ['paper', paperId],
    queryFn: () => getPaperDetail(paperId),
    enabled: !!paperId,
  });
}

export function usePaperCitationNetwork(paperId: string) {
  return useQuery({
    queryKey: ['citation-network', paperId],
    queryFn: async () => {
      const response = await apiClient.get(`/api/v1/recommendations/paper/${paperId}/network`);
      return CitationNetworkSchema.parse(response.data);
    },
    enabled: !!paperId,
  });
}

export function usePapers(limit = 20) {
  return useQuery({
    queryKey: ['papers', limit],
    queryFn: async () => {
      // Use query recommendations with a broad topic or trending
      const response = await apiClient.post('/api/v1/recommendations/query', {
        topics: ['AI'], // Default broad topic
        limit,
      });
      return z.array(RecommendationItemSchema).parse(response.data.recommendations);
    },
  });
}
