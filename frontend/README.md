# GraphLit ResearchRadar — Frontend

Interactive web application for academic paper discovery through citation intelligence, community detection, and personalized recommendations.

## Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Next.js | 16.1.6 | App Router, React Server Components, Turbopack |
| React | 19.x | UI rendering |
| TypeScript | 5.x (strict) | Type safety |
| Bun | 1.3.5+ | Package manager and runtime |
| Tailwind CSS | 4.x | Utility-first styling |
| shadcn/ui | Radix UI | Accessible component primitives |
| TanStack Query | v5 | Async state management (5-min stale, 30-min GC) |
| Zustand | v5 | Client state (minimal usage) |
| @xyflow/react | 12.x | Interactive citation network graphs |
| Recharts | 3.x | Charts (impact distribution, citation trends, topics) |
| Framer Motion | 12.x | Page transitions and animations |
| Axios | 1.x | HTTP client with interceptors |
| Zod | 4.x | Runtime API response validation |
| Biome | 2.x | Linting + formatting |

## Getting Started

```bash
# Install dependencies
bun install

# Configure environment
cp .env.example .env.local
# Edit: NEXT_PUBLIC_API_URL=http://localhost:8080

# Start development server
bun run dev
# → http://localhost:3000
```

**Requires**: Backend API running on port 8080 (see `backend/README.md`).

## Pages

| Route | Page | Features |
|-------|------|----------|
| `/` | Home | Hero section, platform stats, search bar, navigation |
| `/search` | Discovery Engine | Full-text search, temporal range filter, min impact score filter, sort by relevance, paper card grid |
| `/paper/[id]` | Paper Detail | Metadata, abstract, citation graph (React Flow), topic badges, similarity breakdown, recommendations |
| `/communities` | Research Clusters | Community cards with stats, min papers filter, Louvain cluster overview |
| `/communities/[id]` | Cluster Detail | Trending papers, cluster network graph, thematic analytics, temporal filters (All Time/5Y/3Y/2Y), bridging papers |
| `/feed` | Neural Intelligence Feed | Session-based personalized recommendations, history nodes count, global trending momentum, cold start fallback |

## Components (28 total)

**UI Primitives (10)**: badge, button, card, input, select, dialog, alert, skeleton, slider, tabs

**Layout (3)**: Navbar, Footer, SessionManager

**Paper (5)**: PaperCard, PaperCardSkeleton, CitationGraph, TopicBadges, SimilarityBreakdown

**Community (4)**: CommunityCard, CommunityGraph, BridgingPapers, YearFilterToggle

**Search (3)**: SearchBar, AdvancedFilters, EmptyState

**Charts (3)**: CitationTrendChart, ImpactScoreChart, TopicDistribution

## API Integration

All 11 backend endpoints are integrated via Axios with automatic session ID injection (`X-Session-ID` header) and 10-second timeouts.

**React Query hooks**:
- `usePapers` — paper detail, recommendations, citation network
- `useCommunities` — community list, trending, network
- `useRecommendations` — query search, personalized feed, view tracking
- `useStats` — platform statistics

**Caching strategy**: TanStack Query with 5-minute staleTime, 30-minute gcTime. Reduces API calls by ~80% for repeat navigation.

**Session management**: UUID generated on first visit, persisted in localStorage, injected into all API requests. User profiles stored server-side in Neo4j as `UserProfile` nodes.

## Development

```bash
bun run dev                     # Dev server (Turbopack, localhost:3000)
bun run build                   # Production build
bun run start                   # Serve production build
bun run type-check              # TypeScript strict mode
bun run lint                    # Biome linting
bun run lint:fix                # Auto-fix lint issues
bun run format                  # Auto-format code
```

## Architecture

```
src/
├── app/                        # Next.js App Router pages
│   ├── page.tsx                # Home
│   ├── search/page.tsx         # Discovery Engine
│   ├── paper/[id]/page.tsx     # Paper Detail
│   ├── communities/
│   │   ├── page.tsx            # Research Clusters
│   │   └── [id]/page.tsx       # Cluster Detail
│   ├── feed/page.tsx           # Personalized Feed
│   ├── layout.tsx              # Root layout (providers, navbar, footer)
│   ├── globals.css             # Tailwind + custom styles
│   ├── error.tsx               # Error boundary
│   └── loading.tsx             # Loading state
├── components/
│   ├── ui/                     # shadcn/ui primitives
│   ├── layout/                 # Navbar, Footer, SessionManager
│   ├── paper/                  # Paper-specific components
│   ├── community/              # Community-specific components
│   ├── search/                 # Search + filters
│   ├── charts/                 # Recharts visualizations
│   └── providers/              # QueryProvider (React Query)
└── lib/
    ├── api/                    # Axios client, endpoint functions
    ├── hooks/                  # React Query hooks
    ├── utils/                  # Formatters, validators, session, cn
    └── constants.ts            # Shared constants
```

## License

MIT
