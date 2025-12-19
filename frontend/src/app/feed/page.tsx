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
      <header className="space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-3xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-inner">
              <LayoutDashboard className="h-8 w-8 text-primary" />
            </div>
            <div className="space-y-1">
              <h1 className="text-4xl font-black tracking-tighter uppercase italic leading-none">
                Neural <span className="text-primary">Intelligence</span> Feed
              </h1>
              <p className="text-muted-foreground font-bold uppercase text-xs tracking-widest">
                Research curated based on your interaction topology
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <Badge
              variant="outline"
              className="px-4 py-2 font-black gap-2 bg-primary/5 border-primary/20 text-primary uppercase tracking-widest text-[10px]"
            >
              <History className="h-3 w-3" />
              HISTORY NODES: {feedData?.viewing_history_count ?? 0}
            </Badge>
            <Badge
              variant="outline"
              className="px-4 py-2 font-black gap-2 bg-orange-500/5 border-orange-500/20 text-orange-500 uppercase tracking-widest text-[10px]"
            >
              <Zap className="h-3 w-3" />
              SESSION ACTIVE
            </Badge>
          </div>
        </div>
      </header>

      {!hasHistory && !isLoading && (
        <section className="relative p-16 rounded-[3rem] border border-dashed bg-muted/5 text-center space-y-8 overflow-hidden">
          <div className="absolute top-0 right-0 p-12 opacity-5 scale-150">
            <Sparkles className="h-40 w-40" />
          </div>
          <div className="space-y-4 relative z-10 max-w-2xl mx-auto">
            <h2 className="text-3xl font-black italic tracking-tighter uppercase leading-none">
              Cognitive Cold Start <br />
              <span className="text-primary">Detected</span>
            </h2>
            <p className="text-muted-foreground font-medium text-lg italic leading-relaxed">
              We haven't detected enough interaction patterns to curate your neural feed. Explore
              the global research network to initialize your personalized discovery engine.
            </p>
          </div>
          <div className="flex justify-center gap-4 relative z-10">
            <Button
              size="lg"
              asChild
              className="font-black rounded-2xl px-8 shadow-xl shadow-primary/20"
            >
              <Link href="/search">
                Browse Global Network
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </section>
      )}

      <section className="space-y-10">
        <div className="flex items-center justify-between border-b pb-6">
          <div className="flex items-center gap-3">
            <Sparkles className="h-6 w-6 text-primary" />
            <h2 className="text-2xl font-black uppercase tracking-tighter italic">
              {hasHistory ? 'Curated Context Synthesis' : 'Global Trending Momentum'}
            </h2>
          </div>
          {hasHistory && (
            <Badge
              variant="outline"
              className="text-[10px] font-black text-primary uppercase tracking-widest animate-pulse border-primary/50"
            >
              LIVE NEURAL SYNC
            </Badge>
          )}
        </div>

        {isLoading ? (
          <PaperGridSkeleton count={12} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
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
              className="rounded-2xl font-black min-w-[240px] hover:bg-primary hover:text-primary-foreground transition-all uppercase tracking-widest text-xs h-14"
            >
              Synchronize More Nodes
            </Button>
          </div>
        )}
      </section>
    </div>
  );
}
