'use client';

import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowLeft,
  LayoutGrid,
  Network,
  PieChart as PieChartIcon,
  Sparkles,
  TrendingUp,
  Users,
} from 'lucide-react';
import Link from 'next/link';
import { use, useState } from 'react';
import { TopicDistribution } from '@/components/charts/TopicDistribution';
import { BridgingPapers } from '@/components/community/BridgingPapers';
import { CommunityGraph } from '@/components/community/CommunityGraph';
import { YearFilterToggle } from '@/components/community/YearFilterToggle';
import { PaperCard } from '@/components/paper/PaperCard';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useCommunityTrending, useCommunityAnalytics } from '@/lib/hooks/useCommunities';

export default function CommunityDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const communityId = parseInt(id, 10);
  const [minYear, setMinYear] = useState<number | null>(null); // Default: All Time

  const { data: trendingData, isLoading } = useCommunityTrending(communityId, 20, minYear);
  const { data: analyticsData, isLoading: isLoadingAnalytics } = useCommunityAnalytics(communityId);

  return (
    <div className="space-y-12 pb-20">
      <header className="space-y-6">
        <Button
          variant="ghost"
          asChild
          className="p-0 h-auto font-black text-muted-foreground hover:text-primary transition-colors uppercase tracking-widest text-xs"
        >
          <Link href="/communities" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Clusters
          </Link>
        </Button>

        <div className="flex flex-wrap items-end justify-between gap-6">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Badge className="px-3 py-1 bg-primary text-primary-foreground font-black">
                CLUSTER {id}
              </Badge>
              <Badge
                variant="outline"
                className="border-primary/20 bg-primary/5 text-primary font-bold uppercase tracking-widest text-[10px]"
              >
                Thematic Node
              </Badge>
            </div>
            <h1 className="text-5xl md:text-7xl font-black tracking-tighter leading-none uppercase italic">
              Knowledge <br />
              <span className="text-primary">Synthesis</span>
            </h1>
          </div>

          <div className="flex gap-4">
            <div className="p-6 rounded-[2rem] bg-card border text-center min-w-[140px] shadow-sm">
              <div className="text-3xl font-black text-primary italic">
                {trendingData?.total ?? 0}
              </div>
              <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mt-1">
                Cluster Nodes
              </div>
            </div>
          </div>
        </div>
      </header>

      <Tabs defaultValue="papers" className="w-full">
        <TabsList className="bg-secondary/50 p-1 rounded-xl mb-8">
          <TabsTrigger value="papers" className="rounded-lg font-bold uppercase text-xs">
            Trending Papers
          </TabsTrigger>
          <TabsTrigger value="network" className="rounded-lg font-bold uppercase text-xs">
            Cluster Network
          </TabsTrigger>
          <TabsTrigger value="analytics" className="rounded-lg font-bold uppercase text-xs">
            Thematic Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="papers" className="space-y-12">
          {/* Trending Papers */}
          <section className="space-y-8">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b pb-6">
              <div className="space-y-1">
                <h2 className="text-3xl font-black flex items-center gap-3 uppercase tracking-tighter italic">
                  <TrendingUp className="text-primary h-8 w-8" />
                  Cluster Momentum
                </h2>
                <p className="text-muted-foreground font-bold uppercase text-xs tracking-[0.1em]">
                  High-centrality papers defining this thematic cluster
                </p>
              </div>
              <YearFilterToggle value={minYear} onChange={setMinYear} />
            </div>

            {isLoading ? (
              <PaperGridSkeleton count={8} />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <AnimatePresence mode="popLayout">
                  {trendingData?.trending_papers.map((paper, i) => (
                    <motion.div
                      key={paper.paper_id}
                      layout
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.3, delay: i * 0.05 }}
                    >
                      <PaperCard paper={paper} />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </section>

          {/* Bridging Papers */}
          <section>
            <BridgingPapers
              papers={
                trendingData?.trending_papers.filter((p) => (p.pagerank || 0) > 0.05).slice(0, 2) ||
                []
              }
            />
          </section>
        </TabsContent>

        <TabsContent value="network" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-black flex items-center gap-2 uppercase tracking-tighter">
              <Network className="h-5 w-5 text-primary" />
              Intra-Cluster Topology
            </h2>
          </div>
          <CommunityGraph communityId={communityId} minYear={minYear} />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <section className="p-8 rounded-[2.5rem] border bg-card/50 space-y-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2">
                <PieChartIcon className="h-5 w-5 text-primary" />
                Thematic Distribution
              </h3>
              {isLoadingAnalytics ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-muted-foreground">Loading analytics...</div>
                </div>
              ) : analyticsData && analyticsData.topic_distribution.length > 0 ? (
                <TopicDistribution data={analyticsData.topic_distribution} />
              ) : (
                <div className="flex items-center justify-center h-64">
                  <div className="text-muted-foreground">No topic data available</div>
                </div>
              )}
            </section>

            <section className="p-8 rounded-[2.5rem] border bg-card/50 space-y-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2">
                <LayoutGrid className="h-5 w-5 text-primary" />
                Cluster Vitality
              </h3>
              {isLoadingAnalytics ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-muted-foreground">Loading analytics...</div>
                </div>
              ) : analyticsData ? (
                <div className="grid grid-cols-2 gap-4">
                  {[
                    {
                      label: 'Network Density',
                      value: analyticsData.network_density.toFixed(2),
                      icon: Network,
                    },
                    {
                      label: 'Centrality Mode',
                      value: analyticsData.centrality_mode,
                      icon: Sparkles,
                      color: 'text-orange-500',
                    },
                    {
                      label: 'Bridging Nodes',
                      value: `${(analyticsData.bridging_nodes_percent * 100).toFixed(1)}%`,
                      icon: Users,
                    },
                    {
                      label: 'Growth Rate',
                      value: `${analyticsData.growth_rate >= 0 ? '+' : ''}${(analyticsData.growth_rate * 100).toFixed(0)}%`,
                      icon: TrendingUp,
                    },
                  ].map((stat) => (
                    <div key={stat.label} className="p-4 rounded-2xl bg-muted/50 border space-y-2">
                      <stat.icon className="h-4 w-4 text-primary" />
                      <div>
                        <div className="text-[8px] font-black uppercase text-muted-foreground">
                          {stat.label}
                        </div>
                        <div className="text-lg font-black tracking-tight">{stat.value}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32">
                  <div className="text-muted-foreground">No analytics available</div>
                </div>
              )}
            </section>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
