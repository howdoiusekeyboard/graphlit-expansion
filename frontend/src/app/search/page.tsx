'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { useSearchParams } from 'next/navigation';
import { useMemo, useState } from 'react';
import { PaperCard } from '@/components/paper/PaperCard';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { AdvancedFilters } from '@/components/search/AdvancedFilters';
import { EmptyState } from '@/components/search/EmptyState';
import { SearchBar } from '@/components/search/SearchBar';
import { Badge } from '@/components/ui/badge';
import { useQueryRecommendations } from '@/lib/hooks/useRecommendations';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const initialTopic = searchParams.get('topics') || '';

  const [topics, setTopics] = useState<string[]>(initialTopic ? [initialTopic] : []);
  const [yearRange, setYearRange] = useState<[number, number]>([2015, 2025]);
  const [minImpact, setMinImpact] = useState(0);

  const { mutate: search, data: results, isPending } = useQueryRecommendations();

  // Trigger search when filters change
  useMemo(() => {
    if (topics.length > 0 || initialQuery) {
      search({
        topics: topics.length > 0 ? topics : [initialQuery],
        year_min: yearRange[0],
        year_max: yearRange[1],
        limit: 20,
      });
    }
  }, [topics, yearRange, initialQuery, search]);

  const handleClearFilters = () => {
    setTopics([]);
    setYearRange([2015, 2025]);
    setMinImpact(0);
  };

  return (
    <div className="space-y-12 pb-20">
      <header className="space-y-8 text-center max-w-3xl mx-auto">
        <div className="space-y-4">
          <Badge
            variant="outline"
            className="px-4 py-1.5 font-black uppercase tracking-[0.2em] border-primary/20 bg-primary/5 text-primary"
          >
            Discovery Engine
          </Badge>
          <h1 className="text-5xl md:text-7xl font-black tracking-tighter uppercase italic leading-none">
            Uncover Hidden <br />
            <span className="text-primary">Intelligence</span>
          </h1>
          <p className="text-muted-foreground font-medium text-lg italic">
            Explore the citation graph through multi-topic filtering and temporal analysis.
          </p>
        </div>
        <div className="flex justify-center">
          <SearchBar />
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
        {/* Sidebar Filters */}
        <aside className="lg:col-span-1">
          <AdvancedFilters
            topics={topics}
            yearRange={yearRange}
            minImpact={minImpact}
            onTopicsChange={setTopics}
            onYearRangeChange={setYearRange}
            onMinImpactChange={setMinImpact}
            onClear={handleClearFilters}
          />
        </aside>

        {/* Results Area */}
        <main className="lg:col-span-3 space-y-8">
          <div className="flex items-center justify-between border-b pb-4">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-black uppercase tracking-tighter">Research Yield</h2>
              {results && (
                <Badge className="bg-primary text-primary-foreground font-black">
                  {results.total} NODES
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">
                Sorted by
              </span>
              <Badge variant="outline" className="font-bold">
                RELEVANCE
              </Badge>
            </div>
          </div>

          {isPending ? (
            <PaperGridSkeleton count={9} />
          ) : results?.recommendations && results.recommendations.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              <AnimatePresence mode="popLayout">
                {results.recommendations
                  .filter((p) => (p.impact_score || 0) >= minImpact)
                  .map((paper, i) => (
                    <motion.div
                      key={paper.paper_id}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: i * 0.03 }}
                    >
                      <PaperCard paper={paper} />
                    </motion.div>
                  ))}
              </AnimatePresence>
            </div>
          ) : (
            <EmptyState
              title="No Research Nodes Detected"
              description="Adjust your temporal filters or topic keywords to broaden your discovery radius."
              actionLabel="Reset Discovery"
              onAction={handleClearFilters}
            />
          )}
        </main>
      </div>
    </div>
  );
}
