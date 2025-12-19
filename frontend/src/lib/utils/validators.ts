import { z } from 'zod';

// Recommendation breakdown
export const SimilarityBreakdownSchema = z.object({
  citation_overlap: z.number().min(0).max(1),
  topic_affinity: z.number().min(0).max(1),
  author_collaboration: z.number().min(0).max(1),
  citation_velocity: z.number().min(0).max(1),
});

// Paper recommendation item schema
export const RecommendationItemSchema = z.object({
  paper_id: z.string().regex(/^W\d+$/, 'Invalid OpenAlex ID format'),
  title: z.string().min(1),
  year: z.number().int().min(1900).max(2100),
  citations: z.number().int().nonnegative(),
  impact_score: z.number().min(0).max(100),
  similarity_score: z.number().min(0).max(1),
  similarity_breakdown: SimilarityBreakdownSchema.optional(),
  matched_topics: z.array(z.string()).optional(),
  topic_match_count: z.number().optional(),
  relevance_score: z.number().optional(),
  community: z.number().optional(),
  pagerank: z.number().optional(),
  betweenness: z.number().optional(),
  personalized_score: z.number().optional(),
});

// Paper recommendations response schema
export const PaperRecommendationsResponseSchema = z.object({
  recommendations: z.array(RecommendationItemSchema),
  total: z.number().int().nonnegative(),
  cached: z.boolean(),
  cache_ttl_seconds: z.number().int().positive().optional(),
  user_session_id: z.string().optional(),
  viewing_history_count: z.number().optional(),
});

// Query request schema
export const QueryRequestSchema = z.object({
  topics: z.array(z.string()).min(1, 'At least one topic required'),
  year_min: z.number().int().min(1900).max(2100).optional(),
  year_max: z.number().int().min(1900).max(2100).optional(),
  exclude_paper_ids: z.array(z.string()).optional(),
  limit: z.number().int().min(1).max(100).default(20),
});

// Export inferred types
export type RecommendationItem = z.infer<typeof RecommendationItemSchema>;
export type PaperRecommendationsResponse = z.infer<typeof PaperRecommendationsResponseSchema>;
export type QueryRequest = z.infer<typeof QueryRequestSchema>;
export type SimilarityBreakdown = z.infer<typeof SimilarityBreakdownSchema>;
