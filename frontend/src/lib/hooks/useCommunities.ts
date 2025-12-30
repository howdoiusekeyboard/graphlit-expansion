import { useQuery } from '@tanstack/react-query';
import {
  getCommunities,
  getCommunityCitationNetwork,
  getCommunityTrending,
  getCommunityAnalytics,
} from '@/lib/api/communities';

export function useCommunities() {
  return useQuery({
    queryKey: ['communities'],
    queryFn: () => getCommunities(),
  });
}

export function useCommunityTrending(
  communityId: number,
  limit = 20,
  minYear?: number | null,
) {
  return useQuery({
    queryKey: ['community-trending', communityId, limit, minYear],
    queryFn: () => getCommunityTrending(communityId, limit, minYear),
    enabled: !!communityId || communityId === 0,
  });
}

export function useCommunityCitationNetwork(communityId: number, minYear?: number | null) {
  return useQuery({
    queryKey: ['community-network', communityId, minYear],
    queryFn: () => getCommunityCitationNetwork(communityId, minYear),
    enabled: !!communityId || communityId === 0,
  });
}

export function useCommunityAnalytics(communityId: number) {
  return useQuery({
    queryKey: ['community-analytics', communityId],
    queryFn: () => getCommunityAnalytics(communityId),
    enabled: !!communityId || communityId === 0,
    staleTime: 1000 * 60 * 60, // 1 hour - analytics change slowly
  });
}
