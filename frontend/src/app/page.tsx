'use client';

import { motion } from 'framer-motion';
import { ArrowRight, BookOpen, Network, Sparkles, TrendingUp, Users } from 'lucide-react';
import Link from 'next/link';
import { PaperCard } from '@/components/paper/PaperCard';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { Button } from '@/components/ui/button';
import { usePapers } from '@/lib/hooks/usePapers';

import type { RecommendationItem } from '@/lib/utils/validators';

export default function HomePage() {
  const { data: papers, isLoading } = usePapers(6);

  const stats = [
    { label: 'Papers Tracked', value: '1,247', icon: BookOpen },
    { label: 'Communities', value: '42', icon: Network },
    { label: 'Total Citations', value: '15,893', icon: Users },
  ];

  return (
    <div className="space-y-20 pb-20">
      {/* ... Hero Section ... */}
      {/* ... Stats Section ... */}

      {/* Featured Papers */}
      <section className="container space-y-8">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-3xl font-black flex items-center gap-3">
              <TrendingUp className="text-primary h-8 w-8" />
              Featured Papers
            </h2>
            <p className="text-muted-foreground font-medium">
              Top performing research across all communities
            </p>
          </div>
          <Button variant="ghost" asChild className="font-bold">
            <Link href="/search">
              View All
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>

        {isLoading ? (
          <PaperGridSkeleton count={6} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {papers?.map((paper: RecommendationItem, i: number) => (
              <motion.div
                key={paper.paper_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 * i }}
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
