# GraphLit ResearchRadar Frontend

AI-Powered Citation Intelligence for Academic Research.

## Tech Stack
- **Framework**: Next.js 16.1.0 (App Router)
- **Runtime**: Bun 1.3.5
- **Styling**: Tailwind CSS 4.1
- **State Management**: TanStack Query v5, Zustand v5
- **Visualization**: React Flow (Citation Networks), Recharts (Analytics)
- **UI Components**: shadcn/ui (Radix UI)
- **Quality**: Biome (Linting & Formatting)

## Getting Started

1. **Install Dependencies**:
   ```bash
   bun install
   ```

2. **Configure Environment**:
   Create a `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run Development Server**:
   ```bash
   bun run dev
   ```

4. **Build for Production**:
   ```bash
   bun run build
   ```

## Project Features
- **Intelligent Recommendations**: Collaborative filtering based on citation overlap and topic affinity.
- **Citation Networks**: Interactive node-based visualization of paper relationships.
- **Community Detection**: Exploration of research clusters identified via Louvain algorithm.
- **Impact Analytics**: Real-time scoring and distribution tracking.
- **Personalized Feed**: Session-aware research discovery based on viewing history.

## Development Workflows
- **Type Check**: `bun run type-check`
- **Lint & Fix**: `bun run lint:fix`
- **Format**: `bun run format`
