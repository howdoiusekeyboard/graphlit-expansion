import {
  type CommunitiesResponse,
  CommunitiesResponseSchema,
  type TrendingPapersResponse,
  TrendingPapersResponseSchema,
} from '@/lib/utils/validators';
import { type CitationNetwork } from '@/lib/hooks/usePapers';
import { z } from 'zod';
import { apiClient } from './client';

const CitationNetworkResponseSchema = z.object({
  papers: z.array(
    z.object({
      paper_id: z.string(),
      title: z.string(),
      year: z.number().nullable(),
      citations: z.number(),
      impact_score: z.number().nullable(),
      community: z.number().nullable(),
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

export async function getCommunities(): Promise<CommunitiesResponse> {
  const response = await apiClient.get('/api/v1/recommendations/communities');
  return CommunitiesResponseSchema.parse(response.data);
}

export async function getCommunityTrending(
  communityId: number,
  limit = 20,
  minYear?: number | null,
): Promise<TrendingPapersResponse> {
  const params: Record<string, number> = { limit };
  if (minYear !== null && minYear !== undefined) {
    params.min_year = minYear;
  }

  const response = await apiClient.get(
    `/api/v1/recommendations/community/${communityId}/trending`,
    { params },
  );

  return TrendingPapersResponseSchema.parse(response.data);
}

export async function getCommunityCitationNetwork(
  communityId: number,
  minYear?: number | null,
): Promise<CitationNetwork> {
  const params: Record<string, number> = {};
  if (minYear !== null && minYear !== undefined) {
    params.min_year = minYear;
  }

  const response = await apiClient.get(
    `/api/v1/recommendations/community/${communityId}/network`,
    { params },
  );

  return CitationNetworkResponseSchema.parse(response.data);
}
