import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api/client';
import { PaperRecommendationsResponseSchema } from '@/lib/utils/validators';

const CommunitySchema = z.object({
  community_id: z.number(),
  paper_count: z.number(),
  avg_impact_score: z.number(),
  top_topics: z.array(z.string()),
  representative_papers: z.array(
    z.object({
      paper_id: z.string(),
      title: z.string(),
    }),
  ),
});

export type Community = z.infer<typeof CommunitySchema>;

export function useCommunities() {
  return useQuery({
    queryKey: ['communities'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/communities');
      return z.array(CommunitySchema).parse(response.data);
    },
  });
}

export function useCommunityTrending(communityId: number, limit = 20) {
  return useQuery({
    queryKey: ['community-trending', communityId, limit],
    queryFn: async () => {
      const response = await apiClient.get(
        `/api/v1/recommendations/community/${communityId}/trending`,
        {
          params: { limit },
        },
      );
      return PaperRecommendationsResponseSchema.parse(response.data);
    },
    enabled: !!communityId || communityId === 0,
  });
}
