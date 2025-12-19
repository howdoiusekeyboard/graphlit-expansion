import { PaperCard } from '@/components/paper/PaperCard';
import type { RecommendationItem } from '@/lib/utils/validators';

interface BridgingPapersProps {
  papers: RecommendationItem[];
}

export function BridgingPapers({ papers }: BridgingPapersProps) {
  if (papers.length === 0) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold flex items-center gap-2">
        <span className="flex h-2 w-2 rounded-full bg-primary" />
        Bridging Papers
      </h3>
      <p className="text-sm text-muted-foreground">
        These papers have high betweenness centrality, acting as bridges to other research
        communities.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {papers.map((paper) => (
          <PaperCard key={paper.paper_id} paper={paper} />
        ))}
      </div>
    </div>
  );
}
