# GraphLit ResearchRadar Frontend - Production-Grade Implementation

> **Target Model**: Gemini 3.0 Pro High Thinking
> **AI Agent**: Orchid AI Agent Coding IDE
> **Project Structure**: `graphit/frontend/` (sibling to `graphit/backend/`)

---

## 🎯 MISSION OBJECTIVE

You are an **elite full-stack TypeScript engineer** building the frontend for **GraphLit ResearchRadar**, an AI-powered citation intelligence platform for academic research. Your mission is to create a **production-ready, bulletproof, end-to-end frontend** that seamlessly integrates with the existing FastAPI backend.

Build a system that is:
- **Fast**: <1s time-to-interactive, optimized bundle sizes
- **Robust**: Comprehensive error handling, graceful degradation
- **Type-safe**: 100% TypeScript strict mode, zero `any` types
- **Accessible**: WCAG 2.1 AA compliant, keyboard navigable
- **Maintainable**: Clean architecture, consistent patterns, self-documenting code

---

## 📚 TECH STACK (EXACT LATEST STABLE VERSIONS)

### Core Framework & Runtime
```json
{
  "next": "16.0.1",              // React framework with App Router, RSC, Server Actions
  "react": "19.2.0",              // Latest stable with enhanced RSC support
  "react-dom": "19.2.0",
  "typescript": "5.7.2",          // Strict mode enabled
  "bun": "1.3.5"                  // Package manager + runtime (user specified)
}
```

### Styling & UI Components
```json
{
  "tailwindcss": "4.1.0",         // Latest v4 with new @theme directive
  "shadcn/ui": "3.6.2",           // Accessible component library (Radix UI primitives)
  "@radix-ui/react-*": "latest",  // Unstyled accessible primitives
  "lucide-react": "latest",       // Icon system (15,000+ icons)
  "tailwindcss-animate": "latest" // Animation utilities for Tailwind
}
```

### Data Fetching & State Management
```json
{
  "@tanstack/react-query": "5.62.8",  // Async state management, caching, mutations
  "zustand": "5.0.9",                  // Lightweight global state (UI state only)
  "zod": "4.0.0",                      // Runtime type validation & schema generation
  "axios": "1.7.9"                     // HTTP client (or use native fetch)
}
```

### Data Visualization & Graphs
```json
{
  "recharts": "3.5.1",           // Charts (bar, line, pie, area)
  "reactflow": "12.10.0",        // Interactive node-based graphs (citation networks)
  "@xyflow/react": "12.10.0"     // React Flow v12 package name
}
```

### Code Quality & Tooling
```json
{
  "@biomejs/biome": "2.3.10",    // Fast linter + formatter (replaces ESLint + Prettier)
  "@types/node": "latest",
  "@types/react": "latest",
  "@types/react-dom": "latest"
}
```

### Additional Utilities
```json
{
  "clsx": "latest",              // Conditional className utility
  "date-fns": "latest",          // Date formatting
  "use-debounce": "latest",      // Debounced search input
  "react-intersection-observer": "latest"  // Lazy loading, infinite scroll
}
```

---

## 🏗️ COMPLETE PROJECT STRUCTURE

```
graphit/
├── backend/                     # Existing FastAPI backend (DO NOT MODIFY)
│   ├── src/graphlit/
│   ├── tests/
│   ├── pyproject.toml
│   └── ...
│
└── frontend/                    # NEW - You will create this
    ├── app/                     # Next.js 16 App Router
    │   ├── layout.tsx           # Root layout with providers (TanStack Query, theme)
    │   ├── page.tsx             # Home page (hero, search, featured papers)
    │   ├── error.tsx            # Error boundary
    │   ├── loading.tsx          # Global loading state
    │   ├── not-found.tsx        # 404 page
    │   │
    │   ├── paper/
    │   │   └── [id]/
    │   │       ├── page.tsx     # Paper detail + recommendations + citation graph
    │   │       ├── loading.tsx  # Paper detail skeleton
    │   │       └── error.tsx    # Paper-specific error handling
    │   │
    │   ├── communities/
    │   │   ├── page.tsx         # Community grid/list view
    │   │   ├── loading.tsx
    │   │   └── [id]/
    │   │       ├── page.tsx     # Community detail (trending papers, graph)
    │   │       └── loading.tsx
    │   │
    │   ├── search/
    │   │   ├── page.tsx         # Advanced search (topic filters, year range)
    │   │   └── loading.tsx
    │   │
    │   └── feed/
    │       ├── page.tsx         # Personalized feed (session-based)
    │       └── loading.tsx
    │
    ├── components/
    │   ├── ui/                  # shadcn/ui components
    │   │   ├── button.tsx
    │   │   ├── card.tsx
    │   │   ├── input.tsx
    │   │   ├── dialog.tsx
    │   │   ├── alert.tsx
    │   │   ├── badge.tsx
    │   │   ├── skeleton.tsx
    │   │   ├── slider.tsx
    │   │   ├── select.tsx
    │   │   ├── tabs.tsx
    │   │   └── ... (add as needed)
    │   │
    │   ├── paper/
    │   │   ├── PaperCard.tsx           # Paper display card (title, authors, year, metrics)
    │   │   ├── PaperCardSkeleton.tsx   # Loading skeleton
    │   │   ├── RecommendationList.tsx  # List of recommended papers
    │   │   ├── CitationGraph.tsx       # Citation network visualization (React Flow)
    │   │   ├── SimilarityBreakdown.tsx # Pie chart of similarity components
    │   │   └── TopicBadges.tsx         # Clickable topic tags
    │   │
    │   ├── community/
    │   │   ├── CommunityCard.tsx       # Community card (ID, paper count, topics)
    │   │   ├── CommunityGrid.tsx       # Grid of community cards
    │   │   ├── CommunityGraph.tsx      # Intra-community citation graph
    │   │   └── BridgingPapers.tsx      # Papers connecting communities
    │   │
    │   ├── search/
    │   │   ├── SearchBar.tsx           # Global search input (debounced)
    │   │   ├── AdvancedFilters.tsx     # Topic multi-select, year range slider
    │   │   ├── SearchResults.tsx       # Sortable results table
    │   │   └── EmptyState.tsx          # No results found
    │   │
    │   ├── layout/
    │   │   ├── Navbar.tsx              # Top navigation (logo, search, links)
    │   │   ├── Footer.tsx              # Footer with links, credits
    │   │   ├── Sidebar.tsx             # Optional left sidebar (filters)
    │   │   └── MobileNav.tsx           # Mobile hamburger menu
    │   │
    │   ├── charts/
    │   │   ├── ImpactScoreChart.tsx    # Recharts bar chart (impact distribution)
    │   │   ├── CitationTrendChart.tsx  # Line chart (citations over time)
    │   │   └── TopicDistribution.tsx   # Pie chart (topic breakdown)
    │   │
    │   └── providers/
    │       ├── QueryProvider.tsx       # TanStack Query provider
    │       └── ThemeProvider.tsx       # Dark mode provider (optional)
    │
    ├── lib/
    │   ├── api/
    │   │   ├── client.ts               # Axios instance with base URL, interceptors
    │   │   ├── papers.ts               # Paper API functions
    │   │   ├── recommendations.ts      # Recommendation API functions
    │   │   ├── communities.ts          # Community API functions
    │   │   ├── analytics.ts            # Analytics/tracking API
    │   │   └── types.ts                # Generated TypeScript types from backend
    │   │
    │   ├── hooks/
    │   │   ├── usePapers.ts            # React Query hook for papers
    │   │   ├── usePaperDetail.ts       # Single paper fetch
    │   │   ├── useRecommendations.ts   # Recommendation hook
    │   │   ├── useCommunities.ts       # Community data hook
    │   │   ├── useSearch.ts            # Debounced search hook
    │   │   ├── useFeed.ts              # Personalized feed hook
    │   │   ├── useTrackView.ts         # Mutation hook for tracking views
    │   │   └── useLocalStorage.ts      # Session ID persistence
    │   │
    │   ├── utils/
    │   │   ├── cn.ts                   # clsx + tailwind-merge utility
    │   │   ├── formatters.ts           # Date, number, citation formatting
    │   │   ├── validators.ts           # Zod schemas for API responses
    │   │   ├── graph-layout.ts         # Force-directed layout for React Flow
    │   │   └── session.ts              # Session ID generation/management
    │   │
    │   ├── constants.ts                # API URLs, config, feature flags
    │   └── types.ts                    # Shared TypeScript types
    │
    ├── public/
    │   ├── favicon.ico
    │   ├── logo.svg
    │   └── images/
    │
    ├── styles/
    │   └── globals.css                 # Tailwind imports + custom CSS
    │
    ├── .env.local                      # Environment variables (gitignored)
    ├── .env.example                    # Example env file
    ├── biome.json                      # Biome linter/formatter config
    ├── tailwind.config.ts              # Tailwind CSS 4.1 configuration
    ├── tsconfig.json                   # TypeScript strict configuration
    ├── next.config.ts                  # Next.js configuration
    ├── package.json                    # Bun package management
    ├── bun.lockb                       # Bun lockfile
    ├── components.json                 # shadcn/ui configuration
    └── README.md                       # Setup instructions, API docs
```

---

## 🔌 BACKEND API INTEGRATION

### Backend Base URL
```typescript
// lib/constants.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**Note**: Backend runs from `graphit/backend/` but serves on `http://localhost:8000`

---

## 📡 COMPLETE API REFERENCE

### 1. **Paper Recommendations** (Collaborative Filtering)

**Endpoint**: `GET /api/v1/recommendations/paper/{paper_id}`

**Query Parameters**:
- `limit` (integer, 1-50, default: 10) - Number of recommendations
- `min_similarity` (float, 0.0-1.0, default: 0.3) - Minimum similarity threshold

**Response**:
```typescript
interface PaperRecommendationsResponse {
  recommendations: Array<{
    paper_id: string;           // OpenAlex ID format: "W2741809807"
    title: string;              // Paper title
    year: number;               // Publication year
    citations: number;          // Citation count
    impact_score: number;       // Composite impact score (0-100)
    similarity_score: number;   // Overall similarity (0.0-1.0)
    similarity_breakdown?: {
      citation_overlap: number;     // Citation-based similarity (35% weight)
      topic_affinity: number;       // Topic-based similarity (30% weight)
      author_collaboration: number; // Author network similarity (20% weight)
      citation_velocity: number;    // Citation growth similarity (15% weight)
    };
  }>;
  total: number;              // Total recommendations found
  cached: boolean;            // Whether response was cached
  cache_ttl_seconds?: number; // Cache TTL (3600s = 1 hour)
}
```

**Example Request**:
```typescript
const response = await fetch(
  `${API_BASE_URL}/api/v1/recommendations/paper/W2741809807?limit=10&min_similarity=0.5`
);
```

---

### 2. **Query-Based Recommendations** (Topic + Year Filtering)

**Endpoint**: `POST /api/v1/recommendations/query`

**Request Body**:
```typescript
interface QueryRequest {
  topics: string[];              // e.g., ["Machine Learning", "Deep Learning"]
  year_min?: number;             // e.g., 2020 (default: 2015)
  year_max?: number;             // e.g., 2024 (default: current year)
  exclude_paper_ids?: string[];  // Papers to exclude from results
  limit: number;                 // 1-100 (default: 20)
}
```

**Response**:
```typescript
interface QueryRecommendationsResponse {
  recommendations: Array<{
    paper_id: string;
    title: string;
    year: number;
    citations: number;
    impact_score: number;
    matched_topics: string[];       // Topics from query that matched
    topic_match_count: number;      // Number of topics matched
    relevance_score: number;        // Weighted relevance (impact + topic match)
  }>;
  total: number;
  cached: boolean;
}
```

**Example Request**:
```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/recommendations/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topics: ['Graph Neural Networks', 'Recommendation Systems'],
    year_min: 2020,
    year_max: 2024,
    limit: 20,
  }),
});
```

---

### 3. **Community Trending Papers**

**Endpoint**: `GET /api/v1/recommendations/community/{community_id}/trending`

**Query Parameters**:
- `limit` (integer, 1-100, default: 20)

**Response**:
```typescript
interface CommunityTrendingResponse {
  recommendations: Array<{
    paper_id: string;
    title: string;
    year: number;
    citations: number;
    impact_score: number;
    community: number;          // Community ID
    pagerank: number;           // PageRank centrality score
    betweenness?: number;       // Betweenness centrality (bridging papers)
  }>;
  community_id: number;
  total: number;
  cached: boolean;
}
```

---

### 4. **Personalized Feed** (Session-Based)

**Endpoint**: `GET /api/v1/recommendations/feed/{user_session_id}`

**Query Parameters**:
- `limit` (integer, 1-100, default: 20)

**Response**:
```typescript
interface PersonalizedFeedResponse {
  recommendations: Array<{
    paper_id: string;
    title: string;
    year: number;
    citations: number;
    impact_score: number;
    matched_topics: string[];       // Topics inferred from user's viewing history
    personalized_score: number;     // Weighted score based on user preferences
  }>;
  total: number;
  user_session_id: string;
  viewing_history_count: number;    // Number of papers viewed by this session
  cached: boolean;
}
```

**Cold Start**: If `user_session_id` has no viewing history, returns trending papers.

---

### 5. **Track Paper View** (Personalization)

**Endpoint**: `POST /api/v1/recommendations/track/view`

**Request Body**:
```typescript
interface PaperViewEvent {
  user_session_id: string;    // UUID or session identifier
  paper_id: string;           // OpenAlex ID (W-prefixed)
}
```

**Response**: `204 No Content` (success)

**Example Usage**:
```typescript
// Track view when user clicks on a paper card
async function trackPaperView(paperId: string) {
  const sessionId = getOrCreateSessionId(); // From localStorage
  await fetch(`${API_BASE_URL}/api/v1/recommendations/track/view`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_session_id: sessionId,
      paper_id: paperId,
    }),
  });
}
```

---

### 6. **Admin Endpoints** (Cache Management)

**Get Cache Stats**: `GET /api/v1/admin/cache/stats`

**Response**:
```typescript
interface CacheStatsResponse {
  available: boolean;
  hits: number;
  misses: number;
  errors: number;
  sets: number;
  invalidations: number;
  hit_rate: number;           // 0.0-1.0
  keys_count?: number;
  memory_used_mb?: number;
  evicted_keys?: number;
  connected_clients?: number;
}
```

**Invalidate Cache**: `POST /api/v1/admin/cache/invalidate`

**Request Body**:
```typescript
interface InvalidateCacheRequest {
  pattern: string;  // e.g., "recommendations:*", "recommendations:paper:W123456:*"
}
```

---

### 7. **Health Check**

**Endpoint**: `GET /health`

**Response**:
```typescript
interface HealthResponse {
  status: "healthy";
  service: "ResearchRadar API";
}
```

---

## 🎨 COMPREHENSIVE UI/UX REQUIREMENTS

### Page 1: **Home Page** (`app/page.tsx`)

**Hero Section**:
- Large heading: "AI-Powered Citation Intelligence for Academic Research"
- Subheading: "Discover papers through collaborative filtering, community detection, and predictive impact scoring"
- Global search bar (debounced 300ms, searches title, authors, keywords)
- CTA button: "Explore Communities"

**Featured Papers Section**:
- Grid of top 6 papers by impact score
- Each card shows: Title, Authors (first 3), Year, Citations, Impact Score badge
- Skeleton loading states

**Quick Stats Dashboard**:
```
┌────────────────┬────────────────┬────────────────┐
│ 1,247 Papers   │ 42 Communities │ 15,893 Citations│
└────────────────┴────────────────┴────────────────┘
```

**Topic Cloud** (optional):
- Word cloud of most popular research topics (weighted by paper count)
- Click topic → navigate to search with that topic filter

---

### Page 2: **Paper Detail Page** (`app/paper/[id]/page.tsx`)

**Header Section**:
- Paper title (large, bold)
- Authors list (expandable if >5 authors)
- Publication venue, year, DOI link
- Metrics row:
  - Citations count with icon
  - Impact score badge (colored gradient: 0-100)
  - PageRank centrality
  - Community ID (clickable link)

**Abstract Section**:
- Expandable text (initially 3 lines, "Read more" to expand)
- Topics badges (clickable, navigate to search)

**Recommendations Section** ("Papers You Might Find Relevant"):
- Similarity threshold slider (0.3 - 1.0, default: 0.3)
  - Updates recommendations in real-time
- List of recommended papers (PaperCard components)
- Each card shows:
  - Title, authors, year
  - Similarity score bar (visual progress bar)
  - Similarity breakdown (hover tooltip or expandable):
    - Citation Overlap: XX%
    - Topic Affinity: XX%
    - Author Collaboration: XX%
    - Citation Velocity: XX%

**Citation Graph Visualization**:
- Interactive React Flow graph showing:
  - Central node: Current paper (highlighted, larger)
  - Connected nodes: Papers citing this paper + papers cited by this paper
  - Node colors: By community (color-coded)
  - Node sizes: By impact score (larger = higher impact)
  - Edges: Directional arrows (→ cites direction)
- Controls:
  - Zoom in/out
  - Pan
  - Reset view
  - Toggle labels
  - Filter by citation direction (incoming, outgoing, both)
- Legend: Community colors, node size scale

**Tabs** (optional):
- Overview (default, shows above content)
- Full Citations List (paginated table)
- Metrics Breakdown (charts showing impact score components)

---

### Page 3: **Community Explorer** (`app/communities/page.tsx`)

**Header**:
- Title: "Research Communities"
- Description: "Communities detected via Louvain algorithm based on citation patterns"
- Total community count

**View Toggle**:
- Grid view (default) | List view

**Filters Sidebar**:
- Min/Max paper count slider
- Topic keyword search
- Sort by:
  - Paper count (desc)
  - Community ID (asc)
  - Avg impact score (desc)

**Community Grid/List**:
- Each community card shows:
  - Community ID badge
  - Paper count
  - Top 3 topics (with paper counts)
  - Avg impact score
  - Representative papers (top 2 by PageRank)
  - "View Details" button

**Pagination**:
- Show 12 communities per page
- Load more button or infinite scroll

---

### Page 4: **Community Detail** (`app/communities/[id]/page.tsx`)

**Header**:
- Community ID badge (large)
- Paper count
- Top topics (up to 10, as badges)

**Trending Papers Section**:
- Title: "Top Papers in This Community"
- Sorted by PageRank within community
- List of PaperCard components
- Highlight bridging papers (papers connecting to other communities)

**Community Graph Visualization**:
- React Flow graph showing intra-community citations
- All nodes colored same (community color)
- Central nodes (high PageRank) positioned centrally
- Peripheral nodes on edges
- Legend: PageRank size scale

**Related Communities**:
- List of communities connected via bridging papers
- Show community ID, paper count, shared papers count
- Click to navigate to that community

---

### Page 5: **Search Page** (`app/search/page.tsx`)

**Search Header**:
- Search input (auto-focus, debounced 300ms)
- Placeholder: "Search by title, author, or keywords..."

**Advanced Filters Panel** (collapsible sidebar or top bar):
- **Topics**: Multi-select dropdown (or tag input)
  - Autocomplete from backend topics
  - Show selected topics as removable badges
- **Year Range**: Dual-handle slider (e.g., 2015-2024)
  - Show current range values
- **Min Citation Count**: Number input or slider
- **Min Impact Score**: Slider (0-100)
- "Apply Filters" button + "Clear All" button

**Results Section**:
- Results count: "Found 347 papers"
- Sort dropdown:
  - Relevance (default)
  - Year (newest first)
  - Citations (highest first)
  - Impact Score (highest first)
- Results table with columns:
  - Title (clickable, opens paper detail)
  - Authors (first 3)
  - Year
  - Citations
  - Impact Score (badge)
  - Topics (first 3 badges)
- Pagination: 20 results per page

**Empty State**:
- "No papers found matching your criteria"
- Suggestions: "Try broader search terms or fewer filters"
- Button: "Clear all filters"

---

### Page 6: **Personalized Feed** (`app/feed/page.tsx`)

**Header**:
- Title: "Your Personalized Feed"
- Description: "Based on your recent paper views"
- Session info: "Viewing history: X papers"

**Feed Section**:
- List of recommended papers (PaperCard components)
- Each card shows why it's recommended:
  - "Similar to papers you've viewed"
  - "From topics you're interested in: [Topic1, Topic2]"
- Load more button (infinite scroll)

**Empty State** (no viewing history):
- "Start exploring papers to get personalized recommendations"
- Button: "Explore Trending Papers"
- Fallback: Show global trending papers

**Session Management**:
- Store session ID in localStorage: `graphlit_session_id`
- Generate UUID on first visit
- Display session ID (in dev mode only, top-right corner, small text)

---

## 🛠️ IMPLEMENTATION PATTERNS & CODE EXAMPLES

### 1. **API Client Setup** (`lib/api/client.ts`)

```typescript
import axios, { AxiosError, AxiosInstance } from 'axios';
import { API_BASE_URL } from '@/lib/constants';

// Create Axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add session ID, etc.)
apiClient.interceptors.request.use(
  (config) => {
    // Add session ID to headers if available
    const sessionId = localStorage.getItem('graphlit_session_id');
    if (sessionId) {
      config.headers['X-Session-ID'] = sessionId;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (handle errors globally)
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      console.error(`API Error: ${error.response.status}`, error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error: No response received');
    } else {
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);
```

---

### 2. **Type-Safe API Functions** (`lib/api/recommendations.ts`)

```typescript
import { apiClient } from './client';
import {
  PaperRecommendationsResponseSchema,
  QueryRequestSchema,
  type PaperRecommendationsResponse,
  type QueryRequest,
} from '@/lib/utils/validators';

export async function getPaperRecommendations(
  paperId: string,
  limit = 10,
  minSimilarity = 0.3
): Promise<PaperRecommendationsResponse> {
  const response = await apiClient.get(
    `/api/v1/recommendations/paper/${paperId}`,
    {
      params: { limit, min_similarity: minSimilarity },
    }
  );

  // Validate response with Zod
  return PaperRecommendationsResponseSchema.parse(response.data);
}

export async function queryRecommendations(
  request: QueryRequest
): Promise<PaperRecommendationsResponse> {
  // Validate request
  const validatedRequest = QueryRequestSchema.parse(request);

  const response = await apiClient.post(
    '/api/v1/recommendations/query',
    validatedRequest
  );

  return PaperRecommendationsResponseSchema.parse(response.data);
}
```

---

### 3. **Zod Schemas** (`lib/utils/validators.ts`)

```typescript
import { z } from 'zod';

// Paper recommendation item schema
export const RecommendationItemSchema = z.object({
  paper_id: z.string().regex(/^W\d+$/, 'Invalid OpenAlex ID format'),
  title: z.string().min(1),
  year: z.number().int().min(1900).max(2100),
  citations: z.number().int().nonnegative(),
  impact_score: z.number().min(0).max(100),
  similarity_score: z.number().min(0).max(1),
  similarity_breakdown: z.object({
    citation_overlap: z.number().min(0).max(1),
    topic_affinity: z.number().min(0).max(1),
    author_collaboration: z.number().min(0).max(1),
    citation_velocity: z.number().min(0).max(1),
  }).optional(),
});

// Paper recommendations response schema
export const PaperRecommendationsResponseSchema = z.object({
  recommendations: z.array(RecommendationItemSchema),
  total: z.number().int().nonnegative(),
  cached: z.boolean(),
  cache_ttl_seconds: z.number().int().positive().optional(),
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
```

---

### 4. **React Query Hooks** (`lib/hooks/useRecommendations.ts`)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPaperRecommendations, queryRecommendations } from '@/lib/api/recommendations';
import type { QueryRequest } from '@/lib/utils/validators';

// Hook for paper recommendations
export function usePaperRecommendations(
  paperId: string,
  limit = 10,
  minSimilarity = 0.3,
  enabled = true
) {
  return useQuery({
    queryKey: ['recommendations', 'paper', paperId, limit, minSimilarity],
    queryFn: () => getPaperRecommendations(paperId, limit, minSimilarity),
    staleTime: 5 * 60 * 1000,     // 5 minutes (backend cache is 1 hour)
    gcTime: 30 * 60 * 1000,        // 30 minutes (formerly cacheTime)
    retry: 2,
    enabled: enabled && !!paperId,
  });
}

// Hook for query-based recommendations
export function useQueryRecommendations() {
  return useMutation({
    mutationFn: (request: QueryRequest) => queryRecommendations(request),
    onSuccess: (data) => {
      console.log(`Found ${data.total} recommendations`);
    },
    onError: (error) => {
      console.error('Query recommendations failed:', error);
    },
  });
}

// Hook for tracking paper views
export function useTrackPaperView() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ paperId }: { paperId: string }) => {
      const sessionId = getOrCreateSessionId();
      await apiClient.post('/api/v1/recommendations/track/view', {
        user_session_id: sessionId,
        paper_id: paperId,
      });
    },
    onSuccess: () => {
      // Invalidate personalized feed to refresh
      queryClient.invalidateQueries({ queryKey: ['feed'] });
    },
  });
}

// Helper: Get or create session ID
function getOrCreateSessionId(): string {
  let sessionId = localStorage.getItem('graphlit_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('graphlit_session_id', sessionId);
  }
  return sessionId;
}
```

---

### 5. **Citation Graph Component** (`components/paper/CitationGraph.tsx`)

```typescript
'use client';

import { useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { usePaperCitationNetwork } from '@/lib/hooks/usePapers';

interface CitationGraphProps {
  paperId: string;
  className?: string;
}

export function CitationGraph({ paperId, className }: CitationGraphProps) {
  const { data, isLoading, error } = usePaperCitationNetwork(paperId);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Transform API data to React Flow nodes/edges
  const transformData = useCallback(() => {
    if (!data) return;

    const newNodes: Node[] = data.papers.map((paper) => ({
      id: paper.paper_id,
      type: 'default',
      data: {
        label: truncate(paper.title, 40),
        impact: paper.impact_score,
        year: paper.year,
      },
      position: { x: paper.x || 0, y: paper.y || 0 }, // From force layout
      style: {
        background: getCommunityColor(paper.community),
        borderRadius: '8px',
        padding: '10px',
        fontSize: '12px',
        width: Math.max(100, paper.impact_score * 2), // Size by impact
        height: 60,
      },
    }));

    const newEdges: Edge[] = data.citations.map((citation, idx) => ({
      id: `e-${idx}`,
      source: citation.source,
      target: citation.target,
      type: 'smoothstep',
      animated: citation.source === paperId, // Animate edges from current paper
      style: { stroke: '#888', strokeWidth: 1 },
    }));

    setNodes(newNodes);
    setEdges(newEdges);
  }, [data, paperId, setNodes, setEdges]);

  // Transform data when loaded
  useEffect(() => {
    transformData();
  }, [transformData]);

  if (isLoading) {
    return <div className="h-[600px] flex items-center justify-center">Loading graph...</div>;
  }

  if (error) {
    return <Alert variant="destructive">Failed to load citation graph</Alert>;
  }

  return (
    <div className={cn('h-[600px] w-full border rounded-lg', className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectionMode={ConnectionMode.Loose}
        fitView
        minZoom={0.1}
        maxZoom={2}
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={(node) => node.style?.background as string}
          nodeStrokeWidth={3}
          zoomable
          pannable
        />
      </ReactFlow>
    </div>
  );
}

// Helper: Get color by community ID
function getCommunityColor(communityId: number): string {
  const colors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
  ];
  return colors[communityId % colors.length];
}

// Helper: Truncate text
function truncate(text: string, maxLength: number): string {
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
}
```

---

### 6. **Paper Card Component** (`components/paper/PaperCard.tsx`)

```typescript
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { BookOpen, Calendar, TrendingUp, Users } from 'lucide-react';
import type { RecommendationItem } from '@/lib/utils/validators';
import { formatNumber } from '@/lib/utils/formatters';

interface PaperCardProps {
  paper: RecommendationItem;
  showSimilarity?: boolean;
  onTrackView?: (paperId: string) => void;
}

export function PaperCard({ paper, showSimilarity = false, onTrackView }: PaperCardProps) {
  const handleClick = () => {
    onTrackView?.(paper.paper_id);
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <CardTitle className="text-lg">
          <Link
            href={`/paper/${paper.paper_id}`}
            onClick={handleClick}
            className="hover:text-primary hover:underline"
          >
            {paper.title}
          </Link>
        </CardTitle>
        <CardDescription className="flex items-center gap-4 text-sm">
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {paper.year}
          </span>
          <span className="flex items-center gap-1">
            <BookOpen className="h-3 w-3" />
            {formatNumber(paper.citations)} citations
          </span>
          <span className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            Impact: {paper.impact_score.toFixed(1)}
          </span>
        </CardDescription>
      </CardHeader>

      {showSimilarity && paper.similarity_score !== undefined && (
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Similarity Score</span>
              <Badge variant="secondary">{(paper.similarity_score * 100).toFixed(0)}%</Badge>
            </div>

            {/* Similarity score progress bar */}
            <div className="w-full bg-secondary rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${paper.similarity_score * 100}%` }}
              />
            </div>

            {/* Breakdown (if available) */}
            {paper.similarity_breakdown && (
              <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground mt-2">
                <div>Citation: {(paper.similarity_breakdown.citation_overlap * 100).toFixed(0)}%</div>
                <div>Topic: {(paper.similarity_breakdown.topic_affinity * 100).toFixed(0)}%</div>
                <div>Author: {(paper.similarity_breakdown.author_collaboration * 100).toFixed(0)}%</div>
                <div>Velocity: {(paper.similarity_breakdown.citation_velocity * 100).toFixed(0)}%</div>
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
```

---

### 7. **Search with Debouncing** (`components/search/SearchBar.tsx`)

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useDebounce } from 'use-debounce';
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';

export function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [debouncedQuery] = useDebounce(query, 300); // 300ms debounce

  // Navigate to search page when user types
  useEffect(() => {
    if (debouncedQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(debouncedQuery)}`);
    }
  }, [debouncedQuery, router]);

  return (
    <div className="relative w-full max-w-2xl">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        type="search"
        placeholder="Search papers by title, author, or keywords..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="pl-10 pr-4 py-2"
      />
    </div>
  );
}
```

---

### 8. **Loading Skeletons** (`components/paper/PaperCardSkeleton.tsx`)

```typescript
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function PaperCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-3/4 mb-2" /> {/* Title */}
        <div className="flex gap-4">
          <Skeleton className="h-4 w-16" /> {/* Year */}
          <Skeleton className="h-4 w-24" /> {/* Citations */}
          <Skeleton className="h-4 w-20" /> {/* Impact */}
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-2/3" />
      </CardContent>
    </Card>
  );
}

// Usage in list
export function PaperListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <PaperCardSkeleton key={i} />
      ))}
    </div>
  );
}
```

---

## ⚙️ CONFIGURATION FILES

### `package.json`

```json
{
  "name": "graphlit-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "biome check .",
    "lint:fix": "biome check --write .",
    "format": "biome format --write .",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "16.0.1",
    "react": "19.2.0",
    "react-dom": "19.2.0",
    "@tanstack/react-query": "5.62.8",
    "@xyflow/react": "12.10.0",
    "axios": "1.7.9",
    "clsx": "^2.1.1",
    "date-fns": "^4.1.0",
    "lucide-react": "^0.468.0",
    "recharts": "3.5.1",
    "tailwind-merge": "^2.7.1",
    "tailwindcss-animate": "^1.0.7",
    "use-debounce": "^10.0.4",
    "zod": "^4.0.0",
    "zustand": "5.0.9",
    "@radix-ui/react-alert-dialog": "^1.1.4",
    "@radix-ui/react-dialog": "^1.1.4",
    "@radix-ui/react-dropdown-menu": "^2.1.4",
    "@radix-ui/react-select": "^2.1.4",
    "@radix-ui/react-slider": "^1.2.1",
    "@radix-ui/react-tabs": "^1.1.2"
  },
  "devDependencies": {
    "@biomejs/biome": "2.3.10",
    "@types/node": "^22.10.5",
    "@types/react": "^19.0.6",
    "@types/react-dom": "^19.0.3",
    "tailwindcss": "4.1.0",
    "typescript": "5.7.2"
  }
}
```

---

### `biome.json`

```json
{
  "$schema": "https://biomejs.dev/schemas/2.3.10/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  },
  "files": {
    "ignoreUnknown": false,
    "ignore": [".next", "node_modules", "*.lockb"]
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100,
    "lineEnding": "lf"
  },
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "correctness": {
        "noUnusedVariables": "error",
        "noUnusedImports": "error",
        "useExhaustiveDependencies": "warn"
      },
      "style": {
        "useImportType": "error",
        "noNonNullAssertion": "warn"
      },
      "suspicious": {
        "noExplicitAny": "warn",
        "noArrayIndexKey": "warn"
      }
    }
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "trailingComma": "all",
      "semicolons": "always",
      "arrowParentheses": "always"
    }
  }
}
```

---

### `tailwind.config.ts` (Tailwind CSS 4.1)

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
```

---

### `next.config.ts`

```typescript
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  images: {
    remotePatterns: [
      // Add if using external images (e.g., OpenAlex author photos)
    ],
  },
  experimental: {
    typedRoutes: true, // Type-safe routing in Next.js 16
  },
};

export default nextConfig;
```

---

### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    },
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

---

### `styles/globals.css`

```css
@import 'tailwindcss';

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
    font-feature-settings: 'rlig' 1, 'calt' 1;
  }
}
```

---

### `.env.example`

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics, monitoring
# NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

---

## 🚀 INITIALIZATION COMMANDS

```bash
# 1. Navigate to project root
cd graphit

# 2. Create frontend directory
mkdir frontend
cd frontend

# 3. Initialize Next.js 16 with Bun
bun create next-app@16.0.1 . --typescript --tailwind --app --use-bun

# 4. Install all dependencies (exact versions)
bun add react@19.2.0 react-dom@19.2.0
bun add @tanstack/react-query@5.62.8
bun add @xyflow/react@12.10.0
bun add recharts@3.5.1
bun add axios@1.7.9
bun add zod@4.0.0
bun add zustand@5.0.9
bun add clsx tailwind-merge
bun add lucide-react
bun add use-debounce
bun add date-fns
bun add react-intersection-observer

# 5. Install Radix UI primitives (for shadcn/ui)
bun add @radix-ui/react-alert-dialog
bun add @radix-ui/react-dialog
bun add @radix-ui/react-dropdown-menu
bun add @radix-ui/react-select
bun add @radix-ui/react-slider
bun add @radix-ui/react-tabs

# 6. Install dev dependencies
bun add -D @biomejs/biome@2.3.10
bun add -D @types/node@latest
bun add -D @types/react@latest
bun add -D @types/react-dom@latest
bun add -D tailwindcss@4.1.0
bun add -D typescript@5.7.2
bun add -D tailwindcss-animate

# 7. Initialize shadcn/ui
bunx shadcn@latest init

# When prompted:
# - TypeScript: Yes
# - Style: Default
# - Base color: Slate
# - CSS variables: Yes
# - Tailwind prefix: None
# - Import alias: @/*

# 8. Add shadcn/ui components
bunx shadcn@latest add button
bunx shadcn@latest add card
bunx shadcn@latest add input
bunx shadcn@latest add alert
bunx shadcn@latest add dialog
bunx shadcn@latest add badge
bunx shadcn@latest add skeleton
bunx shadcn@latest add slider
bunx shadcn@latest add select
bunx shadcn@latest add tabs

# 9. Initialize Biome
bunx @biomejs/biome init

# 10. Remove conflicting tools (Biome replaces ESLint/Prettier)
bun remove eslint eslint-config-next prettier

# 11. Update package.json scripts (add these)
# "lint": "biome check .",
# "lint:fix": "biome check --write .",
# "format": "biome format --write .",
# "type-check": "tsc --noEmit"

# 12. Create environment file
cp .env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000

# 13. Verify installation
bun run type-check  # Should pass with 0 errors
bun run lint        # Should pass with 0 violations
```

---

## ✅ COMPREHENSIVE ACCEPTANCE CRITERIA

### Functional Requirements

#### Core Features
- ✅ **Home Page**: Hero, search bar, featured papers (top 6 by impact), stats dashboard
- ✅ **Paper Detail**: Metadata, abstract, recommendations with similarity breakdown, citation graph (React Flow)
- ✅ **Community Explorer**: Grid/list view, filters (paper count, topics), pagination
- ✅ **Community Detail**: Trending papers, intra-community graph, related communities
- ✅ **Search**: Advanced filters (topics multi-select, year range, min citations/impact), sortable results
- ✅ **Personalized Feed**: Session-based recommendations, empty state handling, load more

#### API Integration
- ✅ All 7 API endpoints integrated (`/paper/{id}`, `/query`, `/community/{id}/trending`, `/feed/{session_id}`, `/track/view`, `/admin/cache/*`, `/health`)
- ✅ Proper error handling for all requests (network errors, 4xx, 5xx)
- ✅ Response validation with Zod schemas (runtime type safety)
- ✅ Session tracking with localStorage (`graphlit_session_id`)
- ✅ View tracking on paper card clicks (automatic POST `/track/view`)

#### UX Requirements
- ✅ **Loading States**: Skeleton loaders on all async data (no blank screens)
- ✅ **Error States**: User-friendly error messages with retry buttons
- ✅ **Empty States**: Helpful messages when no data (e.g., "No recommendations found")
- ✅ **Debounced Search**: 300ms delay on search input (use-debounce)
- ✅ **Real-time Filters**: Similarity threshold slider updates recommendations instantly
- ✅ **Responsive Design**: Mobile (375px), tablet (768px), desktop (1024px), wide (1920px)
- ✅ **Keyboard Navigation**: All interactive elements accessible via Tab, Enter, Escape

---

### Non-Functional Requirements

#### Performance
- ✅ **Bundle Size**: Initial bundle <500KB gzipped
- ✅ **Time to Interactive**: <2s on 3G network (Lighthouse)
- ✅ **First Contentful Paint**: <1.5s
- ✅ **React Query Caching**: `staleTime` 5min, `gcTime` 30min (reduces redundant API calls by 80%+)
- ✅ **Image Optimization**: Use Next.js `<Image>` component for all images
- ✅ **Code Splitting**: Lazy load heavy components (React Flow graph, Recharts)

#### Accessibility (WCAG 2.1 AA)
- ✅ **Semantic HTML**: Proper heading hierarchy (h1→h2→h3), landmarks (nav, main, footer)
- ✅ **ARIA Labels**: All interactive elements have accessible names
- ✅ **Focus Management**: Visible focus indicators, logical tab order
- ✅ **Color Contrast**: 4.5:1 minimum for normal text, 3:1 for large text
- ✅ **Screen Reader**: All content accessible via screen reader (test with NVDA/VoiceOver)
- ✅ **Keyboard Only**: Full site navigable without mouse

#### Code Quality
- ✅ **TypeScript Strict**: `strict: true`, no `any` types, all functions typed
- ✅ **Biome Compliance**: Zero linting/formatting violations
- ✅ **Type Check**: `tsc --noEmit` passes with 0 errors
- ✅ **Naming Conventions**: camelCase variables, PascalCase components, SCREAMING_SNAKE_CASE constants
- ✅ **File Organization**: Colocate related files (e.g., `PaperCard.tsx` + `PaperCardSkeleton.tsx`)
- ✅ **No Dead Code**: Remove unused imports, variables, components

#### Security (Phase 1 - No Auth)
- ✅ **Environment Variables**: API URL from `NEXT_PUBLIC_API_URL` (not hardcoded)
- ✅ **Input Sanitization**: Zod validates all user inputs (search queries, filters)
- ✅ **XSS Prevention**: React escapes all dynamic content by default
- ✅ **No Secrets in Client**: No API keys, tokens, or credentials in frontend code

---

### Testing & Validation

#### Manual Testing Checklist
- ✅ Navigate to all 6 pages (home, paper detail, communities, community detail, search, feed)
- ✅ Test search with various queries (partial match, no results, special characters)
- ✅ Test filters (topics multi-select, year range, similarity threshold)
- ✅ Test pagination/infinite scroll (load more papers)
- ✅ Test citation graph (zoom, pan, click nodes)
- ✅ Test session persistence (refresh page, session ID should persist)
- ✅ Test responsive design (resize browser, test on mobile device)
- ✅ Test error scenarios (disconnect network, trigger 404/500 from backend)
- ✅ Test loading states (throttle network to 3G, observe skeletons)

#### Automated Validation
```bash
# TypeScript type checking
bun run type-check  # Must pass with 0 errors

# Biome linting
bun run lint        # Must pass with 0 violations

# Biome formatting
bun run format      # Auto-format all files

# Build validation
bun run build       # Must build successfully with 0 warnings
```

#### Lighthouse Audit (Production Build)
```bash
bun run build
bun run start

# Run Lighthouse in Chrome DevTools:
# - Performance: >90
# - Accessibility: >90
# - Best Practices: >90
# - SEO: >80
```

---

## 🎨 DESIGN SYSTEM & STYLE GUIDE

### Color Palette
- **Primary (Blue)**: `hsl(221.2, 83.2%, 53.3%)` - Trust, academic, interactive elements
- **Secondary (Slate)**: `hsl(210, 40%, 96.1%)` - Backgrounds, cards
- **Success (Green)**: `hsl(142, 71%, 45%)` - High impact scores, positive actions
- **Warning (Amber)**: `hsl(38, 92%, 50%)` - Medium impact, alerts
- **Error (Red)**: `hsl(0, 84.2%, 60.2%)` - Low impact, errors

### Typography
- **Headings**: Inter font family (via Next.js font optimization)
  - H1: 2.25rem (36px), font-weight 700
  - H2: 1.875rem (30px), font-weight 600
  - H3: 1.5rem (24px), font-weight 600
- **Body**: 1rem (16px), font-weight 400, line-height 1.5
- **Small Text**: 0.875rem (14px) for metadata, captions

### Spacing Scale (Tailwind)
- `gap-2` (0.5rem/8px): Tight spacing (icon + text)
- `gap-4` (1rem/16px): Default spacing (cards in grid)
- `gap-6` (1.5rem/24px): Section spacing
- `gap-8` (2rem/32px): Large spacing (page sections)

### Component Patterns
- **Cards**: White background, subtle border, hover shadow
- **Buttons**: Primary (filled blue), Secondary (outlined), Ghost (transparent)
- **Badges**: Rounded-full, small text, colored background (topic tags, metrics)
- **Progress Bars**: Horizontal bars for similarity scores (0-100%)
- **Tooltips**: Hover for additional info (similarity breakdown, metrics)

---

## 🚫 CONSTRAINTS & EXCLUSIONS

### DO NOT IMPLEMENT (Out of Scope for Phase 1)
- ❌ **Authentication**: No login, no JWT, no user accounts
- ❌ **Authorization**: No role-based access control, no protected routes
- ❌ **User Profiles**: No saved preferences, no user settings
- ❌ **Social Features**: No comments, no sharing, no likes
- ❌ **Backend Modifications**: Do not modify anything in `graphit/backend/`
- ❌ **Database Access**: Frontend only consumes API, no direct DB connections
- ❌ **Server-Side Sessions**: Use localStorage for session tracking only

### MUST AVOID (Anti-Patterns)
- ❌ **Using Pages Router**: Next.js 16 App Router only (no `pages/` directory)
- ❌ **Client-Only Rendering**: Leverage React Server Components where possible
- ❌ **Mixing Linters**: Do not install ESLint or Prettier (Biome only)
- ❌ **Hardcoded URLs**: Always use `API_BASE_URL` from constants
- ❌ **Ignoring TypeScript Errors**: Fix all type errors, never use `@ts-ignore` or `any`
- ❌ **Large Dependencies**: Avoid heavy libraries (e.g., Moment.js - use date-fns instead)
- ❌ **Inline Styles**: Use Tailwind classes (exception: dynamic styles like graph node colors)
- ❌ **Premature Optimization**: Don't optimize until profiling shows bottleneck

---

## 📖 DOCUMENTATION REFERENCES

Use **Context7 MCP** in Orchid AI Agent to fetch latest documentation:

### Framework & Core Libraries
```
Next.js 16: /vercel/next.js/v16.0.3
React 19: /websites/react_dev
TypeScript: /websites/typescript (official docs)
Bun: Search "bun" in Context7
```

### Styling & UI
```
Tailwind CSS 4.1: /websites/v3_tailwindcss (closest available)
shadcn/ui: Search "shadcn" in Context7
Radix UI: Search "radix-ui" in Context7
```

### Data & State
```
TanStack Query: Search "tanstack query" in Context7
Zod: Search "zod" in Context7
Zustand: Search "zustand" in Context7
```

### Visualization
```
React Flow: Search "reactflow" or "xyflow" in Context7
Recharts: Search "recharts" in Context7
```

### Tooling
```
Biome: /biomejs/biome/_biomejs_biome_2_3_10 (if available)
```

---

## 💡 EXPERT IMPLEMENTATION TIPS

### 1. **Start with API Client Foundation**
Build `lib/api/client.ts` and `lib/api/recommendations.ts` first, then UI. This ensures type-safe data flow.

### 2. **Use Zod for All API Responses**
Generate TypeScript types from Zod schemas:
```typescript
export const PaperSchema = z.object({ /* ... */ });
export type Paper = z.infer<typeof PaperSchema>;
```

### 3. **React Query Best Practices**
- Use `queryKey` arrays for cache invalidation: `['recommendations', 'paper', paperId]`
- Set `staleTime` to match backend cache TTLs (1 hour for recommendations)
- Use `useMutation` for POST/PUT/DELETE (e.g., tracking views)

### 4. **Optimize React Flow for Large Graphs**
```typescript
// Only render nodes in viewport (performance optimization)
import { useViewportNodes } from '@xyflow/react';

const visibleNodes = useViewportNodes(); // Renders only visible nodes
```

### 5. **Debounce All Search Inputs**
```typescript
import { useDebounce } from 'use-debounce';
const [query, setQuery] = useState('');
const [debouncedQuery] = useDebounce(query, 300);
```

### 6. **Always Show Loading Skeletons**
Never show blank screens or spinners alone. Use skeleton placeholders that match final layout.

### 7. **Error Boundaries for Critical Sections**
Wrap React Flow, Recharts, and other heavy components in error boundaries to prevent full-page crashes.

### 8. **Session ID Management**
```typescript
// lib/utils/session.ts
export function getOrCreateSessionId(): string {
  if (typeof window === 'undefined') return ''; // SSR guard

  let sessionId = localStorage.getItem('graphlit_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('graphlit_session_id', sessionId);
  }
  return sessionId;
}
```

### 9. **Accessibility Checklist**
- Use `<button>` for clickable elements (not `<div onClick>`)
- Add `aria-label` to icon-only buttons
- Use semantic HTML (`<nav>`, `<main>`, `<article>`)
- Test with keyboard only (Tab, Enter, Escape, Arrow keys)

### 10. **Performance Monitoring**
```typescript
// app/layout.tsx - Add performance observer
useEffect(() => {
  if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'largest-contentful-paint') {
          console.log('LCP:', entry.renderTime || entry.loadTime);
        }
      }
    });
    observer.observe({ entryTypes: ['largest-contentful-paint'] });
  }
}, []);
```

---

## 📦 DELIVERABLES CHECKLIST

Upon completion, verify all deliverables are present:

### Code Deliverables
- ✅ `graphit/frontend/` directory with complete Next.js 16 project
- ✅ All 6 pages implemented (`app/page.tsx`, `app/paper/[id]/`, `app/communities/`, `app/search/`, `app/feed/`)
- ✅ All 15+ components implemented (`components/paper/`, `components/community/`, `components/ui/`)
- ✅ API client with 7 endpoint integrations (`lib/api/`)
- ✅ React Query hooks for all endpoints (`lib/hooks/`)
- ✅ Zod schemas for type validation (`lib/utils/validators.ts`)
- ✅ Citation graph component with React Flow (`components/paper/CitationGraph.tsx`)
- ✅ Charts with Recharts (`components/charts/`)

### Configuration Files
- ✅ `package.json` with exact versions
- ✅ `biome.json` configured
- ✅ `tailwind.config.ts` with theme
- ✅ `next.config.ts` with env vars
- ✅ `tsconfig.json` strict mode
- ✅ `.env.example` template
- ✅ `components.json` (shadcn/ui config)

### Documentation
- ✅ `README.md` with:
  - Project overview
  - Setup instructions (Bun installation, env vars)
  - Development commands (`dev`, `build`, `lint`, `type-check`)
  - API endpoint documentation (link to backend docs)
  - Project structure explanation
  - Troubleshooting section
- ✅ Inline code comments for complex logic (graph layouts, similarity calculations)
- ✅ JSDoc comments on exported functions/components

### Validation
- ✅ `bun run type-check` passes with 0 errors
- ✅ `bun run lint` passes with 0 violations
- ✅ `bun run build` succeeds with 0 warnings
- ✅ All pages load without errors in browser console
- ✅ Lighthouse score >90 on production build

---

## ✨ SUCCESS METRICS

After implementation, the frontend should demonstrate:

### Technical Excellence
- **Fast**: <1s time-to-interactive on repeat visits (measured with Lighthouse)
- **Reliable**: Graceful error handling, no crashes, 99.9% uptime readiness
- **Type-Safe**: 100% TypeScript strict mode, zero `any` types, full IntelliSense
- **Accessible**: WCAG 2.1 AA compliant, keyboard navigable, screen reader compatible
- **Maintainable**: Clean component structure, consistent patterns, self-documenting code

### User Experience
- **Intuitive**: New users can find papers within 30 seconds of landing
- **Responsive**: Works flawlessly on mobile, tablet, desktop (tested 375px - 1920px)
- **Performant**: Smooth 60fps animations, instant feedback on interactions
- **Helpful**: Clear error messages, empty states guide next steps, tooltips explain metrics

### Data Integrity
- **Accurate**: All API responses validated with Zod (runtime type safety)
- **Cached**: React Query reduces redundant API calls by 80%+
- **Tracked**: User views persisted to backend for personalization
- **Consistent**: Session ID persists across page refreshes

---

## 🎯 FINAL INSTRUCTIONS FOR GEMINI 3.0 PRO HIGH THINKING

You are building a **production-grade research tool** that will be used by academic researchers to discover papers, explore citation networks, and track research communities. This is not a prototype or demo - it must be **bulletproof**.

### Your Priorities (in order):
1. **Correctness**: All API integrations work flawlessly, data is accurate
2. **Type Safety**: Strict TypeScript, Zod validation, zero runtime errors
3. **Performance**: Fast load times, smooth interactions, optimized bundles
4. **Accessibility**: Every researcher can use this tool (keyboard, screen reader, mobile)
5. **Maintainability**: Clean code, consistent patterns, well-documented

### Quality Standards:
- **No shortcuts**: Don't skip loading states, error handling, or accessibility
- **No placeholders**: Every component must be fully functional
- **No mock data**: All data comes from the real backend API
- **No `any` types**: Use proper TypeScript types everywhere
- **No silent failures**: All errors must be logged and displayed to user

### Mindset:
You are building a tool that researchers will rely on to make **critical decisions** about which papers to read, which research areas to explore, and which citations to follow. Your code must be **trustworthy**, **accurate**, and **robust**.

**Think like a senior engineer at a top tech company**. Write code you'd be proud to have reviewed by your peers. Build a system that could scale to 100,000 users and 1 million papers without breaking.

---

## 🚀 READY TO BUILD

You have everything you need:
- ✅ Complete tech stack with exact versions
- ✅ Full API documentation with request/response schemas
- ✅ Comprehensive project structure
- ✅ Code examples for every pattern
- ✅ Configuration files ready to use
- ✅ Clear acceptance criteria
- ✅ Success metrics

**Your task**: Implement this system **end-to-end**, from API client to UI components, from search to citations graphs, from loading states to error handling.

**Build this system to be bulletproof. Build it to last. Build it right.**

**Now go build something amazing.** 🚀

---

**END OF PROMPT**

---

## 📝 NOTES FOR ORCHID AI AGENT

- This prompt is designed for **Gemini 3.0 Pro High Thinking**
- All versions are **latest stable** as of 2025-12-18
- Backend API runs on `http://localhost:8000` (from `graphit/backend/`)
- Frontend will be in `graphit/frontend/` (sibling directory)
- **No authentication/security** implemented in Phase 1 (postponed)
- Focus on **robustness, type safety, and user experience**
- Use **Context7 MCP** for latest documentation lookups during implementation
