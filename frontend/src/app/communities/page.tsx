'use client';

import { motion } from 'framer-motion';
import { Filter, LayoutGrid, List, Users } from 'lucide-react';
import { CommunityCard } from '@/components/community/CommunityCard';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useCommunities } from '@/lib/hooks/useCommunities';

export default function CommunitiesPage() {
  const { data: communities, isLoading } = useCommunities();

  return (
    <div className="space-y-10">
      <header className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-primary/10 text-primary">
            <Users className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-4xl font-black tracking-tight">Research Communities</h1>
            <p className="text-muted-foreground font-medium">
              Clusters discovered via Louvain algorithm based on citation topology
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="font-bold gap-2">
              <Filter className="h-4 w-4" />
              Filter Patterns
            </Button>
            <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest px-4 border-l">
              {communities?.length ?? 0} Clusters Identified
            </span>
          </div>
          <div className="flex bg-muted rounded-lg p-1">
            <Button variant="ghost" size="icon" className="h-8 w-8 bg-background shadow-sm">
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8 opacity-50">
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: Static skeleton list
            <Skeleton key={i} className="h-[400px] rounded-3xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {communities?.map((community, i) => (
            <motion.div
              key={community.community_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
            >
              <CommunityCard community={community} />
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
