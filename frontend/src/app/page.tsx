'use client';

import { motion } from 'framer-motion';
import { ArrowRight, BookOpen, Network, TrendingUp, Users } from 'lucide-react';
import Link from 'next/link';
import { PaperCard } from '@/components/paper/PaperCard';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { SearchBar } from '@/components/search/SearchBar';
import { Button } from '@/components/ui/button';
import { usePapers } from '@/lib/hooks/usePapers';
import { useStats } from '@/lib/hooks/useStats';

import type { RecommendationItem } from '@/lib/utils/validators';

export default function HomePage() {
  const { data: papers, isLoading } = usePapers(6);
  const { data: dbStats } = useStats();

  const stats = [
    {
      label: 'Papers Tracked',
      value: dbStats?.total_papers.toLocaleString() ?? '...',
      icon: BookOpen,
    },
    {
      label: 'Communities',
      value: dbStats?.total_communities.toLocaleString() ?? '...',
      icon: Network,
    },
    {
      label: 'Total Citations',
      value: dbStats?.total_citations.toLocaleString() ?? '...',
      icon: Users,
    },
  ];

  return (
    <div className="space-y-20 pb-20">
      {/* Hero Section */}
      <section className="relative pt-20 pb-16 overflow-hidden">
        <div className="container relative z-10 text-center space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-4"
          >
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-tight">
              Graph DBMS <span className="text-primary">Citation</span> Intelligence
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto font-medium">
              Discover academic breakthroughs through collaborative filtering, community detection,
              and predictive impact scoring.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="max-w-2xl mx-auto pt-4"
          >
            <SearchBar />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex items-center justify-center gap-4 pt-4"
          >
            <Button size="lg" className="rounded-full px-8 font-bold" asChild>
              <Link href="/communities">Explore Communities</Link>
            </Button>
            <Button size="lg" variant="outline" className="rounded-full px-8 font-bold" asChild>
              <Link href="/search">Advanced Search</Link>
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Stats Dashboard */}
      <section className="container">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.4 + i * 0.1 }}
              className="p-8 rounded-3xl bg-secondary/50 border flex flex-col items-center text-center space-y-3"
            >
              <div className="p-4 rounded-2xl bg-primary/10 text-primary">
                <stat.icon className="h-8 w-8" />
              </div>
              <div>
                <div className="text-4xl font-black tracking-tighter">{stat.value}</div>
                <div className="text-sm font-bold text-muted-foreground uppercase tracking-widest">
                  {stat.label}
                </div>
                {stat.label === 'Communities' && (
                  <p className="text-xs text-muted-foreground/70 font-medium italic pt-2">
                    Minimum 3 papers
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

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
