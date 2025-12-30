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
  cache_ttl_seconds: z.number().int().positive().nullable().optional(),
  user_session_id: z.string().optional(),
  viewing_history_count: z.number().optional(),
});

// Query request schema
export const QueryRequestSchema = z.object({
  topics: z.array(z.string()).default([]),
  year_min: z.number().int().min(1900).max(2100).optional(),
  year_max: z.number().int().min(1900).max(2100).optional(),
  exclude_paper_ids: z.array(z.string()).optional(),
  limit: z.number().int().min(1).max(100).default(20),
});

// Paper detail schema
export const PaperDetailItemSchema = z.object({
  paper_id: z.string().regex(/^W\d+$/, 'Invalid OpenAlex ID format'),
  title: z.string().min(1),
  year: z.number().int().min(1900).max(2100).nullable(),
  citations: z.number().int().nonnegative(),
  impact_score: z.number().min(0).max(100).nullable(),
  abstract: z.string().nullable(),
  doi: z.string().nullable(),
  community: z.number().nullable(),
  topics: z.array(z.string()),
});

// Community list item schema
export const CommunityListItemSchema = z.object({
  id: z.number().int(),
  paper_count: z.number().int().nonnegative(),
  avg_impact: z.number().nullable(),
  top_topics: z.array(z.string()),
});

// Communities response schema
export const CommunitiesResponseSchema = z.object({
  communities: z.array(CommunityListItemSchema),
  total: z.number().int().nonnegative(),
});

// Trending paper item schema (for community trending endpoint)
export const TrendingPaperItemSchema = z.object({
  paper_id: z.string().regex(/^W\d+$/, 'Invalid OpenAlex ID format'),
  title: z.string().min(1),
  year: z.number().int().min(1900).max(2100),
  citations: z.number().int().nonnegative(),
  impact_score: z.number().min(0).max(100).nullable(),
  pagerank: z.number().nullable(),
  community: z.number().optional(),
});

// Trending papers response schema (for community trending endpoint)
export const TrendingPapersResponseSchema = z.object({
  community_id: z.number().int(),
  community_label: z.string().nullable(),
  trending_papers: z.array(TrendingPaperItemSchema),
  total: z.number().int().nonnegative(),
});

// Topic distribution item schema
export const TopicDistributionItemSchema = z.object({
  name: z.string(),
  value: z.number().int().nonnegative(),
  paper_count: z.number().int().nonnegative(),
});

// Community analytics response schema
export const CommunityAnalyticsResponseSchema = z.object({
  network_density: z.number().min(0).max(1),
  centrality_mode: z.string(),
  avg_pagerank: z.number(),
  bridging_nodes_percent: z.number().min(0).max(1),
  growth_rate: z.number(),
  topic_distribution: z.array(TopicDistributionItemSchema),
  total_papers: z.number().int().nonnegative(),
});

// Export inferred types
export type RecommendationItem = z.infer<typeof RecommendationItemSchema>;
export type PaperRecommendationsResponse = z.infer<typeof PaperRecommendationsResponseSchema>;
export type PaperDetailItem = z.infer<typeof PaperDetailItemSchema>;
export type CommunityListItem = z.infer<typeof CommunityListItemSchema>;
export type CommunitiesResponse = z.infer<typeof CommunitiesResponseSchema>;
export type QueryRequest = z.infer<typeof QueryRequestSchema>;
export type SimilarityBreakdown = z.infer<typeof SimilarityBreakdownSchema>;
export type TrendingPaperItem = z.infer<typeof TrendingPaperItemSchema>;
export type TrendingPapersResponse = z.infer<typeof TrendingPapersResponseSchema>;
export type TopicDistributionItem = z.infer<typeof TopicDistributionItemSchema>;
export type CommunityAnalyticsResponse = z.infer<typeof CommunityAnalyticsResponseSchema>;
