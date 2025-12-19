'use client';

import { AnimatePresence, motion } from 'framer-motion';
import {
  BarChart3,
  BookOpen,
  Calendar,
  ExternalLink,
  Info,
  Network,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { use, useEffect, useState } from 'react';
import { CitationTrendChart } from '@/components/charts/CitationTrendChart';
import { ImpactScoreChart } from '@/components/charts/ImpactScoreChart';
import { CitationGraph } from '@/components/paper/CitationGraph';
import { PaperCard } from '@/components/paper/PaperCard';
import { SimilarityBreakdown } from '@/components/paper/SimilarityBreakdown';
import { TopicBadges } from '@/components/paper/TopicBadges';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="bg-secondary/50 p-1 rounded-xl mb-8">
          <TabsTrigger value="overview" className="rounded-lg font-bold uppercase text-xs">
            Overview
          </TabsTrigger>
          <TabsTrigger value="network" className="rounded-lg font-bold uppercase text-xs">
            Citation Network
          </TabsTrigger>
          <TabsTrigger value="metrics" className="rounded-lg font-bold uppercase text-xs">
            Intelligence Metrics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
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

              {/* Discovery Results */}
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
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
                    {[1, 2, 3, 4].map((i) => (
                      <div key={i} className="h-48 bg-muted rounded-3xl" />
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <AnimatePresence mode="popLayout">
                      {recData?.recommendations.slice(0, 6).map((recPaper, i) => (
                        <motion.div
                          key={recPaper.paper_id}
                          layout
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.9 }}
                          transition={{ duration: 0.3, delay: i * 0.05 }}
                        >
                          <PaperCard paper={recPaper} showSimilarity />
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                )}
              </section>
            </div>

            {/* Sidebar - Recommendations Controls */}
            <aside className="space-y-8 lg:sticky lg:top-24 h-fit">
              <section className="p-8 rounded-[2.5rem] border bg-card/50 backdrop-blur-sm space-y-8">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-black tracking-tight uppercase">
                    Intelligence Tuner
                  </h2>
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
                    Adjust threshold to filter discovery results based on multi-dimensional
                    similarity vectors.
                  </p>
                </div>

                {recData?.recommendations[0]?.similarity_breakdown && (
                  <div className="pt-6 border-t">
                    <SimilarityBreakdown
                      breakdown={recData.recommendations[0].similarity_breakdown}
                    />
                  </div>
                )}
              </section>
            </aside>
          </div>
        </TabsContent>

        <TabsContent value="network">
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
          </section>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-12">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            <section className="p-8 rounded-[2.5rem] border bg-card/50 space-y-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Citation Growth Velocity
              </h3>
              <CitationTrendChart
                data={[
                  { year: (paper.year ?? 2024) - 2, citations: Math.floor(paper.citations * 0.05) },
                  { year: (paper.year ?? 2024) - 1, citations: Math.floor(paper.citations * 0.2) },
                  { year: paper.year ?? 2024, citations: paper.citations },
                ]}
              />
            </section>
            <section className="p-8 rounded-[2.5rem] border bg-card/50 space-y-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                Impact Distribution (Cohort)
              </h3>
              <ImpactScoreChart
                data={[
                  { range: '0-20', count: 12 },
                  { range: '21-40', count: 45 },
                  { range: '41-60', count: 89 },
                  { range: '61-80', count: 34 },
                  { range: '81-100', count: 15 },
                ]}
              />
            </section>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
