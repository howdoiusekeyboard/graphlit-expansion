'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { ChevronDown, Filter, LayoutGrid, Search, Table as TableIcon, X } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';
import { PaperCard } from '@/components/paper/PaperCard';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { useQueryRecommendations } from '@/lib/hooks/useRecommendations';

function SearchContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  const [topics, setTopics] = useState<string[]>(initialQuery ? [initialQuery] : []);
  const [yearRange, setYearRange] = useState([2015, 2024]);
  const [limit, setLimit] = useState(20);

  const { mutate: search, data, isPending } = useQueryRecommendations();

  const handleSearch = useCallback(() => {
    if (topics.length === 0) return;
    search({
      topics,
      year_min: yearRange[0],
      year_max: yearRange[1],
      limit,
    });
  }, [search, topics, yearRange, limit]);

  // Trigger initial search if query exists
  useEffect(() => {
    if (topics.length > 0) {
      handleSearch();
    }
  }, [topics.length, handleSearch]);

  return (
    <div className="space-y-10">
      <header className="space-y-6">
        <h1 className="text-4xl font-black tracking-tight">Advanced Research Discovery</h1>

        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[300px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Add research topic (e.g. Graph Neural Networks)..."
              className="pl-10 h-12 rounded-2xl bg-muted/50 focus-visible:bg-background"
              onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                if (e.key === 'Enter' && e.currentTarget.value) {
                  setTopics([...new Set([...topics, e.currentTarget.value])]);
                  e.currentTarget.value = '';
                }
              }}
            />
          </div>
          <Button size="lg" className="h-12 rounded-2xl font-black px-8" onClick={handleSearch}>
            SEARCH ENGINE
          </Button>
        </div>

        <div className="flex flex-wrap gap-2">
          {topics.map((topic) => (
            <Badge
              key={topic}
              variant="secondary"
              className="px-3 py-1 rounded-full font-bold bg-primary/10 text-primary border-primary/20 gap-2"
            >
              {topic}
              <X
                className="h-3 w-3 cursor-pointer hover:text-destructive"
                onClick={() => setTopics(topics.filter((t) => t !== topic))}
              />
            </Badge>
          ))}
          {topics.length === 0 && (
            <span className="text-sm text-muted-foreground font-medium italic">
              No topics selected. Type above and press Enter.
            </span>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
        {/* Filters Sidebar */}
        <aside className="space-y-8">
          <div className="p-6 rounded-3xl border bg-card/50 backdrop-blur-sm space-y-8">
            <div className="flex items-center gap-2 border-b pb-4">
              <Filter className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-black uppercase tracking-widest">Discovery Filters</h2>
            </div>

            <div className="space-y-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-black uppercase tracking-widest text-muted-foreground">
                    Year Range
                  </span>
                  <span className="text-xs font-bold">
                    {yearRange[0]} - {yearRange[1]}
                  </span>
                </div>
                <Slider
                  aria-label="Year Range"
                  value={yearRange}
                  min={1990}
                  max={2025}
                  step={1}
                  onValueChange={setYearRange}
                  className="py-2"
                />
              </div>

              <div className="space-y-4">
                <span className="text-xs font-black uppercase tracking-widest text-muted-foreground">
                  Result Limit
                </span>
                <div className="grid grid-cols-3 gap-2">
                  {[20, 50, 100].map((val) => (
                    <Button
                      key={val}
                      variant={limit === val ? 'default' : 'outline'}
                      size="sm"
                      className="font-black text-[10px]"
                      onClick={() => setLimit(val)}
                    >
                      {val}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t space-y-4">
                <Button
                  variant="outline"
                  className="w-full font-black text-xs h-10 rounded-xl"
                  onClick={() => {
                    setTopics([]);
                    setYearRange([2015, 2024]);
                    setLimit(20);
                  }}
                >
                  RESET ALL
                </Button>
              </div>
            </div>
          </div>
        </aside>

        {/* Results Area */}
        <div className="lg:col-span-3 space-y-8">
          <div className="flex items-center justify-between border-b pb-4">
            <div className="flex items-center gap-4 text-xs font-black uppercase tracking-widest text-muted-foreground">
              <span>{data?.recommendations.length ?? 0} MATCHES FOUND</span>
              <span className="px-4 border-l">SORT BY RELEVANCE</span>
              <ChevronDown className="h-3 w-3 -ml-3" />
            </div>
            <div className="flex bg-muted rounded-lg p-1">
              <Button variant="ghost" size="icon" className="h-8 w-8 bg-background shadow-sm">
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8 opacity-50">
                <TableIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {isPending ? (
            <PaperGridSkeleton count={9} />
          ) : data?.recommendations && data.recommendations.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              <AnimatePresence mode="popLayout">
                {data.recommendations.map((paper, i) => (
                  <motion.div
                    key={paper.paper_id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: i * 0.03 }}
                  >
                    <PaperCard paper={paper} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <div className="h-[400px] flex flex-col items-center justify-center text-center space-y-4 bg-muted/20 rounded-3xl border border-dashed">
              <div className="p-4 rounded-full bg-muted/50 text-muted-foreground">
                <Search className="h-8 w-8" />
              </div>
              <div className="space-y-1">
                <h3 className="font-black text-lg">No Results Pattern Detected</h3>
                <p className="text-sm text-muted-foreground font-medium max-w-xs mx-auto">
                  Try adjusting your topic nodes or broadening the temporal range filters.
                </p>
              </div>
              <Button
                variant="outline"
                className="font-black text-xs mt-4"
                onClick={() => setTopics(['Machine Learning', 'AI'])}
              >
                TRY SAMPLE TOPICS
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="container py-20 text-center font-bold">Loading discovery engine...</div>
      }
    >
      <SearchContent />
    </Suspense>
  );
}
