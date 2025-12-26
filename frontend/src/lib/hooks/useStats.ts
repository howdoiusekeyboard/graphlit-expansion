/**
 * Hook for fetching database statistics
 */

import { useQuery } from '@tanstack/react-query';
import { getDatabaseStats } from '../api/admin';

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: getDatabaseStats,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: false,
  });
}
