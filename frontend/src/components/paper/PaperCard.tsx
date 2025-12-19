'use client';

import { BookOpen, Calendar, ChevronRight, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useTrackPaperView } from '@/lib/hooks/useRecommendations';
import { formatNumber } from '@/lib/utils/formatters';
import type { RecommendationItem } from '@/lib/utils/validators';

interface PaperCardProps {
  paper: RecommendationItem;
  showSimilarity?: boolean;
}

export function PaperCard({ paper, showSimilarity = false }: PaperCardProps) {
  const { mutate: trackView } = useTrackPaperView();

  const handleClick = () => {
    trackView({ paperId: paper.paper_id });
  };

  return (
    <Card className="group hover:shadow-xl transition-all duration-300 border-muted-foreground/10 hover:border-primary/50 bg-card/50 backdrop-blur-sm overflow-hidden flex flex-col h-full">
      <CardHeader className="flex-1">
        <div className="flex justify-between items-start gap-2 mb-2">
          <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">
            {paper.paper_id}
          </Badge>
          <div className="flex items-center gap-1 text-xs font-semibold text-orange-500">
            <TrendingUp className="h-3 w-3" />
            <span>Impact: {paper.impact_score.toFixed(1)}</span>
          </div>
        </div>
        <CardTitle className="text-lg leading-tight group-hover:text-primary transition-colors line-clamp-2">
          <Link href={`/paper/${paper.paper_id}`} onClick={handleClick}>
            {paper.title}
          </Link>
        </CardTitle>
        <CardDescription className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs mt-2">
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {paper.year}
          </span>
          <span className="flex items-center gap-1">
            <BookOpen className="h-3 w-3" />
            {formatNumber(paper.citations)} citations
          </span>
        </CardDescription>
      </CardHeader>

      {showSimilarity && paper.similarity_score !== undefined && (
        <CardContent className="pt-0">
          <div className="space-y-3 pt-4 border-t border-muted-foreground/10">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground font-medium">Relevance Match</span>
              <span className="text-primary font-bold">
                {(paper.similarity_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-primary h-full transition-all duration-500 ease-out rounded-full"
                style={{ width: `${paper.similarity_score * 100}%` }}
              />
            </div>
            {paper.similarity_breakdown && (
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px] text-muted-foreground">
                <div className="flex justify-between">
                  <span>Citations</span>
                  <span>{(paper.similarity_breakdown.citation_overlap * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Topics</span>
                  <span>{(paper.similarity_breakdown.topic_affinity * 100).toFixed(0)}%</span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      )}

      <div className="px-6 py-3 bg-muted/30 mt-auto flex justify-end group-hover:bg-primary/5 transition-colors">
        <Link
          href={`/paper/${paper.paper_id}`}
          onClick={handleClick}
          className="text-xs font-bold flex items-center gap-1 text-muted-foreground group-hover:text-primary"
        >
          View Details
          <ChevronRight className="h-3 w-3 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </Card>
  );
}
