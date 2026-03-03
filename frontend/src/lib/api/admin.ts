/**
 * Admin API endpoints for database statistics
 */

import { z } from 'zod';
import { apiClient } from './client';

const DatabaseStatsSchema = z.object({
  total_papers: z.number().int().nonnegative(),
  total_communities: z.number().int().nonnegative(),
  total_citations: z.number().int().nonnegative(),
  total_authors: z.number().int().nonnegative(),
  total_topics: z.number().int().nonnegative(),
  papers_with_communities: z.number().int().nonnegative(),
});

export type DatabaseStats = z.infer<typeof DatabaseStatsSchema>;

/**
 * Get real-time database statistics
 */
export async function getDatabaseStats(): Promise<DatabaseStats> {
  const response = await apiClient.get('/api/v1/admin/stats');
  return DatabaseStatsSchema.parse(response.data);
}
