import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getPaperRecommendations, queryRecommendations, trackPaperView } from '@/lib/api/papers';
import { getPersonalizedFeed } from '@/lib/api/recommendations';
import { getOrCreateSessionId } from '@/lib/utils/session';
import type { QueryRequest } from '@/lib/utils/validators';

// Hook for paper recommendations
export function usePaperRecommendations(
  paperId: string,
  limit = 10,
  minSimilarity = 0.3,
  enabled = true,
) {
  return useQuery({
    queryKey: ['recommendations', 'paper', paperId, limit, minSimilarity],
    queryFn: () => getPaperRecommendations(paperId, limit, minSimilarity),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && !!paperId,
  });
}

// Hook for query-based recommendations
export function useQueryRecommendations() {
  return useMutation({
    mutationFn: (request: QueryRequest) => queryRecommendations(request),
  });
}

// Hook for personalized feed
export function useFeed(limit = 20) {
  const sessionId = getOrCreateSessionId();
  return useQuery({
    queryKey: ['feed', sessionId, limit],
    queryFn: () => getPersonalizedFeed(sessionId, limit),
    staleTime: 5 * 60 * 1000,
    enabled: !!sessionId,
  });
}

// Hook for tracking paper views
export function useTrackPaperView() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ paperId }: { paperId: string }) => {
      const sessionId = getOrCreateSessionId();
      await trackPaperView(paperId, sessionId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feed'] });
    },
  });
}
