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
import { use, useEffect, useState } from 'react';
import { CitationGraph } from '@/components/paper/CitationGraph';
import { PaperCard } from '@/components/paper/PaperCard';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { SimilarityBreakdown } from '@/components/paper/SimilarityBreakdown';
import { TopicBadges } from '@/components/paper/TopicBadges';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { usePaperDetail } from '@/lib/hooks/usePapers';
import { usePaperRecommendations, useTrackPaperView } from '@/lib/hooks/useRecommendations';
import { formatNumber } from '@/lib/utils/formatters';

export default function PaperDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [minSimilarity, setMinSimilarity] = useState(0.3);

  const { data: paper, isLoading: isPaperLoading } = usePaperDetail(id);
  const { data: recData, isLoading: isRecLoading } = usePaperRecommendations(id, 12, minSimilarity);
  const { mutate: trackView } = useTrackPaperView();

  useEffect(() => {
    if (id) {
      trackView({ paperId: id });
    }
  }, [id, trackView]);

  if (isPaperLoading) {
    return (
      <div className="space-y-12 animate-pulse">
        <div className="h-40 bg-muted rounded-3xl" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          <div className="lg:col-span-2 h-96 bg-muted rounded-3xl" />
          <div className="h-96 bg-muted rounded-3xl" />
        </div>
      </div>
    );
  }

  if (!paper) return null;

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
              {paper.community !== null && (
                <Badge variant="secondary" className="font-bold">
                  Community Cluster {paper.community}
                </Badge>
              )}
            </div>
            <h1 className="text-3xl md:text-5xl font-black tracking-tight leading-tight uppercase italic">
              {paper.title}
            </h1>
            <div className="flex flex-wrap items-center gap-6 text-sm font-medium text-muted-foreground">
              <span className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-primary" />
                Published {paper.year || 'N/A'}
              </span>
              <span className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-primary" />
                {formatNumber(paper.citations)} Citations
              </span>
              {paper.impact_score !== null && (
                <span className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-orange-500" />
                  Impact Score: {paper.impact_score.toFixed(1)}
                </span>
              )}
              {paper.doi && (
                <Button variant="link" asChild className="p-0 h-auto font-bold text-primary">
                  <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noreferrer">
                    View on DOI.org
                    <ExternalLink className="ml-1 h-3 w-3" />
                  </a>
                </Button>
              )}
            </div>
            <TopicBadges topics={paper.topics} className="pt-2" />
          </div>
        </div>
      </section>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        <div className="lg:col-span-2 space-y-12">
          {/* Abstract */}
          {paper.abstract && (
            <section className="space-y-4">
              <h2 className="text-xl font-black flex items-center gap-2 uppercase tracking-tighter">
                <Info className="h-5 w-5 text-primary" />
                Research Abstract
              </h2>
              <p className="text-muted-foreground leading-relaxed text-lg italic border-l-4 border-primary/20 pl-6 py-2">
                {paper.abstract}
              </p>
            </section>
          )}

          {/* Citation Graph */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-black flex items-center gap-2 uppercase tracking-tighter">
                <Network className="h-5 w-5 text-primary" />
                Citation Network Visualization
              </h2>
              <Badge variant="outline" className="text-[10px] font-bold uppercase">
                Interactive Neural Flow
              </Badge>
            </div>
            <CitationGraph paperId={id} />
            <p className="text-xs text-muted-foreground text-center font-bold uppercase tracking-widest opacity-50">
              * Nodes represent papers, sized by impact score. Colors indicate Louvain communities.
            </p>
          </section>
        </div>

        {/* Sidebar - Recommendations Controls */}
        <aside className="space-y-8 lg:sticky lg:top-24 h-fit">
          <section className="p-8 rounded-[2.5rem] border bg-card/50 backdrop-blur-sm space-y-8">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-black tracking-tight uppercase">Intelligence Tuner</h2>
            </div>

            <div className="space-y-6">
              <div className="flex justify-between items-end">
                <span className="text-xs font-black uppercase tracking-widest text-muted-foreground">
                  Similarity Threshold
                </span>
                <span className="text-3xl font-black text-primary tracking-tighter">
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
              <p className="text-[10px] text-muted-foreground leading-relaxed font-bold uppercase tracking-tight">
                Adjust threshold to filter discovery results based on multi-dimensional similarity
                vectors.
              </p>
            </div>

            {recData?.recommendations[0]?.similarity_breakdown && (
              <div className="pt-6 border-t">
                <SimilarityBreakdown breakdown={recData.recommendations[0].similarity_breakdown} />
              </div>
            )}

            <div className="pt-6 border-t space-y-4">
              <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                <span className="text-muted-foreground">Cache Registry</span>
                <span className="text-primary italic">OPTIMIZED SYNC</span>
              </div>
              <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                <span className="text-muted-foreground">Discovery Yield</span>
                <span>{recData?.total ?? 0} NODES</span>
              </div>
            </div>
          </section>
        </aside>
      </div>

      {/* Recommendations Section */}
      <section className="space-y-8">
        <div className="space-y-1">
          <h2 className="text-2xl font-black tracking-tighter uppercase italic">
            Relevant Research Discovery
          </h2>
          <p className="text-muted-foreground font-bold uppercase text-xs tracking-widest">
            AI-matched papers based on high-dimensional citation context
          </p>
        </div>

        {isRecLoading ? (
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
