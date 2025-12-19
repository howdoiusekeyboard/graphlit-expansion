import { useQuery } from '@tanstack/react-query';
import { getCommunities, getCommunityTrending } from '@/lib/api/communities';

export function useCommunities() {
  return useQuery({
    queryKey: ['communities'],
    queryFn: () => getCommunities(),
  });
}

export function useCommunityTrending(communityId: number, limit = 20) {
  return useQuery({
    queryKey: ['community-trending', communityId, limit],
    queryFn: () => getCommunityTrending(communityId, limit),
    enabled: !!communityId || communityId === 0,
  });
}
