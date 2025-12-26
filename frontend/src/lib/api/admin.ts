/**
 * Admin API endpoints for database statistics
 */

import { apiClient } from './client';

export interface DatabaseStats {
  total_papers: number;
  total_communities: number;
  total_citations: number;
  total_authors: number;
  total_topics: number;
  papers_with_communities: number;
}

/**
 * Get real-time database statistics
 */
export async function getDatabaseStats(): Promise<DatabaseStats> {
  const response = await apiClient.get<DatabaseStats>('/api/v1/admin/stats');
  return response.data;
}
