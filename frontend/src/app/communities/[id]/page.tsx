'use client';

import { motion } from 'framer-motion';
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
          className="p-0 h-auto font-bold text-muted-foreground hover:text-primary transition-colors"
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
                className="border-primary/20 bg-primary/5 text-primary font-bold"
              >
                Thematic Node
              </Badge>
            </div>
            <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-none">
              Thematic Research <br />
              Discovery Center
            </h1>
          </div>

          <div className="flex gap-4">
            <div className="p-4 rounded-2xl bg-card border text-center min-w-[120px]">
              <div className="text-2xl font-black text-primary">{trendingData?.total ?? 0}</div>
              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-tighter">
                Cluster Papers
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-card border text-center min-w-[120px]">
              <div className="text-2xl font-black text-orange-500">89.4</div>
              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-tighter">
                Avg impact
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="p-6 rounded-3xl bg-muted/30 border border-muted-foreground/10 space-y-2">
          <Network className="h-6 w-6 text-primary" />
          <h3 className="font-black text-sm uppercase tracking-widest">Network Density</h3>
          <p className="text-2xl font-black">0.84</p>
        </div>
        <div className="p-6 rounded-3xl bg-muted/30 border border-muted-foreground/10 space-y-2">
          <Sparkles className="h-6 w-6 text-primary" />
          <h3 className="font-black text-sm uppercase tracking-widest">Centrality Mode</h3>
          <p className="text-2xl font-black text-orange-500">PageRank</p>
        </div>
        <div className="p-6 rounded-3xl bg-muted/30 border border-muted-foreground/10 space-y-2">
          <Users className="h-6 w-6 text-primary" />
          <h3 className="font-black text-sm uppercase tracking-widest">Bridging Nodes</h3>
          <p className="text-2xl font-black">12.4%</p>
        </div>
        <div className="p-6 rounded-3xl bg-muted/30 border border-muted-foreground/10 space-y-2">
          <LayoutGrid className="h-6 w-6 text-primary" />
          <h3 className="font-black text-sm uppercase tracking-widest">Sub-communities</h3>
          <p className="text-2xl font-black">5 Nodes</p>
        </div>
      </section>

      {/* Trending Papers */}
      <section className="space-y-8">
        <div className="flex items-center justify-between border-b pb-4">
          <div className="space-y-1">
            <h2 className="text-2xl font-black flex items-center gap-3">
              <TrendingUp className="text-primary h-6 w-6" />
              Trending in This Cluster
            </h2>
            <p className="text-muted-foreground font-medium">
              Ranked by citation velocity and intra-community centrality
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="font-black text-xs">
              EXPORT CSV
            </Button>
            <Button size="sm" className="font-black text-xs">
              VISUALIZE NETWORK
            </Button>
          </div>
        </div>

        {isLoading ? (
          <PaperGridSkeleton count={8} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {trendingData?.recommendations.map((paper, i) => (
              <motion.div
                key={paper.paper_id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
              >
                <PaperCard paper={paper} />
              </motion.div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
