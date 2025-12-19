import {
  type PaperRecommendationsResponse,
  PaperRecommendationsResponseSchema,
} from '@/lib/utils/validators';
import { apiClient } from './client';

export async function getPersonalizedFeed(
  sessionId: string,
  limit = 20,
): Promise<PaperRecommendationsResponse> {
  const response = await apiClient.get(`/api/v1/recommendations/feed/${sessionId}`, {
    params: { limit },
  });

  return PaperRecommendationsResponseSchema.parse(response.data);
}
