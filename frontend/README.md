# GraphLit ResearchRadar — Frontend

Interactive web application for academic paper discovery through citation intelligence, community detection, and personalized recommendations.

## Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Next.js | 16.1.6 | App Router, React Server Components, Turbopack |
| React | 19.2.4 | UI rendering |
| TypeScript | 5.x (strict) | Type safety |
| Bun | 1.3.x | Package manager and runtime |
| Tailwind CSS | 4.2.1 | Utility-first styling |
| shadcn/ui | Radix UI | Accessible component primitives |
| TanStack Query | 5.90.21 | Async state management (5-min stale, 30-min GC) |
| @xyflow/react | 12.10.1 | Interactive citation network graphs |
| react-force-graph | 1.29.x | 2D/3D cluster network visualization |
| Recharts | 3.7.0 | Charts (impact distribution, citation trends, topics) |
| Framer Motion | 12.34.3 | Page transitions and animations |
| Axios | 1.13.6 | HTTP client with interceptors |
| Zod | 4.3.6 | Runtime API response validation |
| Biome | 2.4.4 | Linting + formatting |
| ESLint | 9.39.x | Next.js + TypeScript lint rules |

## Getting Started

```bash
# Install dependencies
bun install

# Configure environment
cp .env.example .env.local
# Edit: NEXT_PUBLIC_API_URL=https://api.graphlit.kushagragolash.tech

# Start development server
bun run dev
# → http://localhost:3000
```

**Requires**: Backend API running (see `backend/README.md`).

**Production URLs**:
- Frontend: `https://graphlit.kushagragolash.tech` (Vercel)
- Backend API: `https://api.graphlit.kushagragolash.tech` (Koyeb)

## Pages

| Route | Page | Features |
|-------|------|----------|
| `/` | Home | Hero section, platform stats, search bar, navigation |
| `/search` | Discovery Engine | Full-text search, temporal range filter, min impact score filter, sort by relevance, paper card grid |
| `/paper/[id]` | Paper Detail | Metadata, abstract, citation graph (React Flow), topic badges, similarity breakdown, recommendations |
| `/communities` | Research Clusters | Community cards with stats, min papers filter, Louvain cluster overview |
| `/communities/[id]` | Cluster Detail | Trending papers, 2D/3D cluster network graph, thematic analytics, temporal filters (All Time/5Y/3Y/2Y), bridging papers |
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
npx eslint .                    # ESLint (Next.js + TypeScript rules)
```

## Architecture

```text
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
