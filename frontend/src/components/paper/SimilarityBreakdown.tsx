import { cn } from '@/lib/utils/cn';
import type { SimilarityBreakdown as SimilarityBreakdownType } from '@/lib/utils/validators';

interface SimilarityBreakdownProps {
  breakdown: SimilarityBreakdownType;
  className?: string;
}

export function SimilarityBreakdown({ breakdown, className }: SimilarityBreakdownProps) {
  const metrics = [
    { label: 'Citation Overlap', value: breakdown.citation_overlap, color: 'bg-blue-500' },
    { label: 'Topic Affinity', value: breakdown.topic_affinity, color: 'bg-emerald-500' },
    { label: 'Author Network', value: breakdown.author_collaboration, color: 'bg-orange-500' },
    { label: 'Citation Velocity', value: breakdown.citation_velocity, color: 'bg-purple-500' },
  ];

  return (
    <div className={cn('space-y-3', className)}>
      <h4 className="text-xs font-black uppercase tracking-widest text-muted-foreground">
        Similarity Breakdown
      </h4>
      <div className="grid grid-cols-1 gap-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="space-y-1.5">
            <div className="flex justify-between text-[10px] font-bold uppercase tracking-tighter">
              <span>{metric.label}</span>
              <span>{(metric.value * 100).toFixed(0)}%</span>
            </div>
            <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
              <div
                className={cn('h-full transition-all duration-500 ease-out', metric.color)}
                style={{ width: `${metric.value * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
