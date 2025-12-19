import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api/client';

const CitationNetworkSchema = z.object({
  papers: z.array(
    z.object({
      paper_id: z.string(),
      title: z.string(),
      year: z.number(),
      citations: z.number(),
      impact_score: z.number(),
      community: z.number(),
      x: z.number().optional(),
      y: z.number().optional(),
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

export function usePaperCitationNetwork(paperId: string) {
  return useQuery({
    queryKey: ['citation-network', paperId],
    queryFn: async () => {
      const response = await apiClient.get(`/api/v1/papers/${paperId}/network`);
      return CitationNetworkSchema.parse(response.data);
    },
    enabled: !!paperId,
  });
}

export function usePapers(limit = 20) {
  return useQuery({
    queryKey: ['papers', limit],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/papers', { params: { limit } });
      return z.array(z.any()).parse(response.data);
    },
  });
}
