'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { ArrowRight, History, LayoutDashboard, Sparkles, Zap } from 'lucide-react';
import Link from 'next/link';
import { PaperCard } from '@/components/paper/PaperCard';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useFeed } from '@/lib/hooks/useRecommendations';

export default function FeedPage() {
  const { data: feedData, isLoading } = useFeed(30);

  const hasHistory = (feedData?.viewing_history_count ?? 0) > 0;

  return (
    <div className="space-y-12 pb-20">
      <header className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-primary/10 text-primary">
            <LayoutDashboard className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-4xl font-black tracking-tight">Personalized Intelligence Feed</h1>
            <p className="text-muted-foreground font-medium">
              Research recommendations curated based on your neural interaction history
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4 pt-4 border-t">
          <Badge
            variant="outline"
            className="px-3 py-1 font-bold gap-2 bg-primary/5 border-primary/20 text-primary"
          >
            <History className="h-3 w-3" />
            HISTORY NODES: {feedData?.viewing_history_count ?? 0}
          </Badge>
          <Badge
            variant="outline"
            className="px-3 py-1 font-bold gap-2 bg-orange-500/5 border-orange-500/20 text-orange-500"
          >
            <Zap className="h-3 w-3" />
            SESSION ACTIVE
          </Badge>
        </div>
      </header>

      {!hasHistory && !isLoading && (
        <section className="relative p-12 rounded-[2.5rem] border border-dashed bg-muted/10 text-center space-y-6 overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-5">
            <Sparkles className="h-40 w-40" />
          </div>
          <div className="space-y-2 relative z-10">
            <h2 className="text-2xl font-black italic">Cognitive Cold Start Detected</h2>
            <p className="text-muted-foreground font-medium max-w-lg mx-auto leading-relaxed">
              We haven't detected enough interaction patterns to curate your neural feed. Explore
              the global research network to initialize your personalized discovery engine.
            </p>
          </div>
          <div className="flex justify-center gap-4 relative z-10">
            <Button size="lg" asChild className="font-black rounded-2xl">
              <Link href="/search">
                Browse Global Network
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </section>
      )}

      <section className="space-y-8">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-black flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-primary" />
            {hasHistory ? 'Curated for Your Context' : 'Global Trending Patterns'}
          </h2>
          {hasHistory && (
            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest border px-3 py-1 rounded-full">
              LIVE NEURAL SYNC
            </span>
          )}
        </div>

        {isLoading ? (
          <PaperGridSkeleton count={12} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <AnimatePresence mode="popLayout">
              {feedData?.recommendations.map((paper, i) => (
                <motion.div
                  key={paper.paper_id}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: i * 0.02 }}
                >
                  <PaperCard paper={paper} showSimilarity={hasHistory} />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}

        {!isLoading && feedData?.recommendations && feedData.recommendations.length > 0 && (
          <div className="flex justify-center pt-12">
            <Button
              variant="outline"
              size="lg"
              className="rounded-2xl font-black min-w-[200px] hover:bg-primary hover:text-primary-foreground transition-all"
            >
              LOAD MORE PATTERNS
            </Button>
          </div>
        )}
      </section>
    </div>
  );
}
