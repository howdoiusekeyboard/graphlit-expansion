import {
  type PaperDetailItem,
  PaperDetailItemSchema,
  type PaperRecommendationsResponse,
  PaperRecommendationsResponseSchema,
  type QueryRequest,
  QueryRequestSchema,
} from '@/lib/utils/validators';
import { apiClient } from './client';

export async function getPaperDetail(paperId: string): Promise<PaperDetailItem> {
  const response = await apiClient.get(`/api/v1/recommendations/paper/${paperId}/detail`);
  return PaperDetailItemSchema.parse(response.data);
}

export async function getPaperRecommendations(
  paperId: string,
  limit = 10,
  minSimilarity = 0.3,
): Promise<PaperRecommendationsResponse> {
  const response = await apiClient.get(`/api/v1/recommendations/paper/${paperId}`, {
    params: { limit, min_similarity: minSimilarity },
  });

  return PaperRecommendationsResponseSchema.parse(response.data);
}

export async function queryRecommendations(
  request: QueryRequest,
): Promise<PaperRecommendationsResponse> {
  const validatedRequest = QueryRequestSchema.parse(request);
  const response = await apiClient.post('/api/v1/recommendations/query', validatedRequest);

  return PaperRecommendationsResponseSchema.parse(response.data);
}

export async function trackPaperView(paperId: string, sessionId: string): Promise<void> {
  await apiClient.post('/api/v1/recommendations/track/view', {
    user_session_id: sessionId,
    paper_id: paperId,
  });
}
