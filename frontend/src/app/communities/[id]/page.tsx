'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeft, LayoutGrid, Network, Sparkles, TrendingUp, Users } from 'lucide-react';
import Link from 'next/link';
import { use } from 'react';
import { PaperCard } from '@/components/paper/PaperCard';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useCommunityTrending } from '@/lib/hooks/useCommunities';

export default function CommunityDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const communityId = parseInt(id, 10);

  const { data: trendingData, isLoading } = useCommunityTrending(communityId);

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

      {/* Stats Section */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Network Density', value: '0.84', icon: Network },
          { label: 'Centrality Mode', value: 'PageRank', icon: Sparkles, color: 'text-orange-500' },
          { label: 'Bridging Nodes', value: '12.4%', icon: Users },
          { label: 'Sub-communities', value: '5 Nodes', icon: LayoutGrid },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-8 rounded-[2.5rem] bg-muted/30 border border-muted-foreground/10 space-y-4 group hover:bg-muted/50 transition-colors"
          >
            <stat.icon className="h-6 w-6 text-primary group-hover:scale-110 transition-transform" />
            <div className="space-y-1">
              <h3 className="font-black text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {stat.label}
              </h3>
              <p className={`text-2xl font-black tracking-tight ${stat.color || ''}`}>
                {stat.value}
              </p>
            </div>
          </motion.div>
        ))}
      </section>

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
          <div className="flex gap-3">
            <Button
              variant="outline"
              size="sm"
              className="rounded-xl font-black text-[10px] uppercase tracking-widest px-6"
            >
              Export Metrics
            </Button>
            <Button
              size="sm"
              className="rounded-xl font-black text-[10px] uppercase tracking-widest px-6 shadow-lg shadow-primary/20"
            >
              Visualize Graph
            </Button>
          </div>
        </div>

        {isLoading ? (
          <PaperGridSkeleton count={8} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <AnimatePresence mode="popLayout">
              {trendingData?.recommendations.map((paper, i) => (
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
    </div>
  );
}
