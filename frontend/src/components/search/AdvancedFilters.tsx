import { Calendar, Tag, TrendingUp } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';

interface AdvancedFiltersProps {
  topics: string[];
  yearRange: [number, number];
  minImpact: number;
  onTopicsChange: (topics: string[]) => void;
  onYearRangeChange: (range: [number, number]) => void;
  onMinImpactChange: (impact: number) => void;
  onClear: () => void;
}

export function AdvancedFilters({
  topics,
  yearRange,
  minImpact,
  onTopicsChange,
  onYearRangeChange,
  onMinImpactChange,
  onClear,
}: AdvancedFiltersProps) {
  return (
    <div className="space-y-8 p-6 rounded-3xl border bg-card/50 backdrop-blur-sm sticky top-24">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-black tracking-tight">Discovery Filters</h3>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onClear}
          className="text-xs font-bold text-muted-foreground hover:text-destructive"
        >
          CLEAR ALL
        </Button>
      </div>

      {/* Year Range */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
            <Calendar className="h-3 w-3" />
            Temporal Range
          </p>
          <span className="text-xs font-black text-primary">
            {yearRange[0]} - {yearRange[1]}
          </span>
        </div>
        <Slider
          aria-label="Year Range"
          value={[yearRange[0], yearRange[1]]}
          min={1990}
          max={2025}
          step={1}
          onValueChange={(v) => onYearRangeChange([v[0] || 1990, v[1] || 2025])}
          className="py-4"
        />
      </div>

      {/* Min Impact */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
            <TrendingUp className="h-3 w-3" />
            Min Impact Score
          </p>
          <span className="text-xs font-black text-orange-500">{minImpact}%</span>
        </div>
        <Slider
          aria-label="Min Impact Score"
          value={[minImpact]}
          min={0}
          max={100}
          step={5}
          onValueChange={(v) => onMinImpactChange(v[0] || 0)}
          className="py-4"
        />
      </div>

      {/* Topics */}
      <div className="space-y-4">
        <p className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
          <Tag className="h-3 w-3" />
          Active Topics
        </p>
        <div className="flex flex-wrap gap-2">
          {topics.length > 0 ? (
            topics.map((topic) => (
              <Badge
                key={topic}
                className="bg-primary text-primary-foreground font-bold pr-1 flex items-center gap-1 group"
              >
                {topic}
                <button
                  type="button"
                  onClick={() => onTopicsChange(topics.filter((t) => t !== topic))}
                  className="hover:bg-primary-foreground hover:text-primary rounded-full p-0.5 transition-colors"
                >
                  <span className="sr-only">Remove {topic}</span>
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <title>Remove topic</title>
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </Badge>
            ))
          ) : (
            <p className="text-[10px] font-bold text-muted-foreground italic">
              No topics selected. Global search active.
            </p>
          )}
        </div>
      </div>

      <div className="pt-6 border-t">
        <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10">
          <p className="text-[10px] font-bold text-primary leading-relaxed uppercase tracking-tighter">
            * Filters are applied in real-time to the current research graph view.
          </p>
        </div>
      </div>
    </div>
  );
}
