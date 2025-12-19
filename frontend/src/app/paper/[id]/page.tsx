'use client';

import { AnimatePresence, motion } from 'framer-motion';
import {
  BookOpen,
  Calendar,
  ExternalLink,
  Info,
  Network,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { use, useState } from 'react';
import { CitationGraph } from '@/components/paper/CitationGraph';
import { PaperCard } from '@/components/paper/PaperCard';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { usePaperRecommendations } from '@/lib/hooks/useRecommendations';

export default function PaperDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [minSimilarity, setMinSimilarity] = useState(0.3);

  // In a real app, we'd fetch the paper detail first.
  // For now, we'll use the recommendation list to simulate having details if the paper is in the list,
  // or we'll just show the metrics from the recommendations.
  const { data: recData, isLoading } = usePaperRecommendations(id, 12, minSimilarity);

  return (
    <div className="space-y-12 pb-20">
      {/* Header Section */}
      <section className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-4 max-w-4xl">
            <div className="flex items-center gap-3">
              <Badge
                variant="outline"
                className="px-3 py-1 text-primary border-primary/20 bg-primary/5 font-black uppercase tracking-widest"
              >
                Paper ID: {id}
              </Badge>
              <Badge variant="secondary" className="font-bold">
                OpenAlex W-Series
              </Badge>
            </div>
            <h1 className="text-3xl md:text-5xl font-black tracking-tight leading-tight">
              Intelligence Systemic Analysis of Citation Patterns
            </h1>
            <div className="flex flex-wrap items-center gap-6 text-sm font-medium text-muted-foreground">
              <span className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-primary" />
                Published 2024
              </span>
              <span className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-primary" />
                1,248 Citations
              </span>
              <span className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-orange-500" />
                Impact Score: 94.2
              </span>
              <Button variant="link" className="p-0 h-auto font-bold text-primary">
                View on DOI.org
                <ExternalLink className="ml-1 h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        <div className="lg:col-span-2 space-y-12">
          {/* Abstract */}
          <section className="space-y-4">
            <h2 className="text-xl font-black flex items-center gap-2">
              <Info className="h-5 w-5 text-primary" />
              Research Overview
            </h2>
            <p className="text-muted-foreground leading-relaxed text-lg italic border-l-4 border-primary/20 pl-6 py-2">
              This research explores the intersection of graph neural networks and collaborative
              filtering, proposing a novel architecture for high-dimensional citation intelligence.
              By leveraging community detection algorithms, we uncover hidden thematic clusters
              within academic literature.
            </p>
          </section>

          {/* Citation Graph */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-black flex items-center gap-2">
                <Network className="h-5 w-5 text-primary" />
                Citation Network Visualization
              </h2>
              <Badge variant="outline" className="text-[10px] font-bold">
                INTERACTIVE FLOW
              </Badge>
            </div>
            <CitationGraph paperId={id} />
            <p className="text-xs text-muted-foreground text-center font-medium">
              * Nodes represent papers, sized by impact score. Colors indicate Louvain communities.
            </p>
          </section>
        </div>

        {/* Sidebar - Recommendations Controls */}
        <aside className="space-y-8 lg:sticky lg:top-24 h-fit">
          <section className="p-6 rounded-3xl border bg-card/50 backdrop-blur-sm space-y-6">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-black tracking-tight">Recommendation Tuner</h2>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-end">
                <span className="text-sm font-bold text-muted-foreground">
                  Similarity Threshold
                </span>
                <span className="text-2xl font-black text-primary">
                  {(minSimilarity * 100).toFixed(0)}%
                </span>
              </div>
              <Slider
                aria-label="Similarity Threshold"
                value={[minSimilarity]}
                min={0.1}
                max={1.0}
                step={0.05}
                onValueChange={(v: number[]) => setMinSimilarity(v[0] || 0.3)}
                className="py-4"
              />
              <p className="text-[10px] text-muted-foreground leading-relaxed font-medium">
                Adjust the threshold to filter papers based on citation overlap, topic affinity, and
                author collaboration similarity.
              </p>
            </div>

            <div className="pt-4 border-t space-y-4">
              <div className="flex justify-between text-xs font-bold">
                <span className="text-muted-foreground uppercase tracking-widest">
                  Cache Status
                </span>
                <span className="text-green-500">OPTIMIZED</span>
              </div>
              <div className="flex justify-between text-xs font-bold">
                <span className="text-muted-foreground uppercase tracking-widest">
                  Results Found
                </span>
                <span>{recData?.total ?? 0}</span>
              </div>
            </div>
          </section>
        </aside>
      </div>

      {/* Recommendations Section */}
      <section className="space-y-8">
        <div className="space-y-1">
          <h2 className="text-2xl font-black tracking-tight">Relevant Research Discovery</h2>
          <p className="text-muted-foreground font-medium">
            AI-matched papers based on current citation context
          </p>
        </div>

        {isLoading ? (
          <PaperGridSkeleton count={4} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <AnimatePresence mode="popLayout">
              {recData?.recommendations.map((paper, i) => (
                <motion.div
                  key={paper.paper_id}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                >
                  <PaperCard paper={paper} showSimilarity />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </section>
    </div>
  );
}
