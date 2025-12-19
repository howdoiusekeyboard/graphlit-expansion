import {
  type CommunitiesResponse,
  CommunitiesResponseSchema,
  type PaperRecommendationsResponse,
  PaperRecommendationsResponseSchema,
} from '@/lib/utils/validators';
import { apiClient } from './client';

export async function getCommunities(): Promise<CommunitiesResponse> {
  const response = await apiClient.get('/api/v1/recommendations/communities');
  return CommunitiesResponseSchema.parse(response.data);
}

export async function getCommunityTrending(
  communityId: number,
  limit = 20,
): Promise<PaperRecommendationsResponse> {
  const response = await apiClient.get(
    `/api/v1/recommendations/community/${communityId}/trending`,
    {
      params: { limit },
    },
  );

  return PaperRecommendationsResponseSchema.parse(response.data);
}
