'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Filter, LayoutGrid, Sparkles, TrendingUp } from 'lucide-react';
import { CommunityCard } from '@/components/community/CommunityCard';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { useCommunities } from '@/lib/hooks/useCommunities';

export default function CommunitiesPage() {
  const { data, isLoading } = useCommunities();
  const [minPapers, setMinPapers] = useState<number>(3);

  // Filter communities client-side
  const filteredCommunities = data?.communities.filter(
    (community) => community.paper_count >= minPapers
  );

  return (
    <div className="space-y-12 pb-20">
      <header className="space-y-4 max-w-3xl">
        <Badge
          variant="outline"
          className="px-4 py-1.5 font-black uppercase tracking-[0.2em] border-primary/20 bg-primary/5 text-primary"
        >
          Community Discovery
        </Badge>
        <h1 className="text-5xl md:text-7xl font-black tracking-tighter uppercase italic leading-none">
          Research <br />
          <span className="text-primary">Clusters</span>
        </h1>
        <p className="text-muted-foreground font-medium text-lg italic">
          Explore thematic neighborhoods detected via Louvain community detection on the global
          citation network.
        </p>
      </header>

      {/* Filter Control */}
      <div className="flex items-center gap-6 p-6 rounded-3xl border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <Filter className="h-5 w-5 text-primary" />
          <label
            htmlFor="min-papers-filter"
            className="text-xs font-black uppercase tracking-widest text-muted-foreground"
          >
            Min Papers
          </label>
        </div>

        <Input
          id="min-papers-filter"
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          value={minPapers}
          onChange={(e) => {
            const value = e.target.value.replace(/\D/g, '');
            const num = value === '' ? 1 : parseInt(value, 10);
            if (num >= 1 && num <= 999) {
              setMinPapers(num);
            }
          }}
          className="w-24 text-center font-black"
          aria-label="Minimum papers per community"
        />

        <span className="text-xs text-muted-foreground font-medium italic">
          Showing {filteredCommunities?.length ?? 0} of {data?.total ?? 0} clusters
        </span>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={`skeleton-${i + 1}`} className="h-64 rounded-[2.5rem]" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredCommunities?.map((community, i) => (
            <motion.div
              key={community.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: i * 0.05 }}
            >
              <CommunityCard community={community} />
            </motion.div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredCommunities?.length === 0 && (
        <div className="text-center py-16 space-y-4">
          <p className="text-lg font-black text-muted-foreground uppercase tracking-wider">
            No clusters match filter
          </p>
          <p className="text-sm text-muted-foreground font-medium italic">
            Try lowering the minimum paper threshold
          </p>
        </div>
      )}

      {/* Stats Footer */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-12 border-t">
        <div className="space-y-2">
          <TrendingUp className="h-8 w-8 text-primary" />
          <h3 className="text-lg font-black uppercase tracking-tighter">Impact Velocity</h3>
          <p className="text-sm text-muted-foreground font-medium italic">
            Trending clusters show high citation acceleration in the last 12 months.
          </p>
        </div>
        <div className="space-y-2">
          <LayoutGrid className="h-8 w-8 text-primary" />
          <h3 className="text-lg font-black uppercase tracking-tighter">Modular Topology</h3>
          <p className="text-sm text-muted-foreground font-medium italic">
            Each cluster represents a distinct research field with high intra-citation density.
          </p>
        </div>
        <div className="space-y-2">
          <Sparkles className="h-8 w-8 text-primary" />
          <h3 className="text-lg font-black uppercase tracking-tighter">Neural Synthesis</h3>
          <p className="text-sm text-muted-foreground font-medium italic">
            Automated topic labeling extracted from cluster-wide abstract synthesis.
          </p>
        </div>
      </section>
    </div>
  );
}
