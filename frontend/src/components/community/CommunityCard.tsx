'use client';

import { BookOpen, ChevronRight, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import type { Community } from '@/lib/hooks/useCommunities';

export function CommunityCard({ community }: { community: Community }) {
  return (
    <Card className="group hover:shadow-xl transition-all duration-300 bg-card/50 backdrop-blur-sm border-muted-foreground/10 hover:border-primary/50 flex flex-col h-full overflow-hidden">
      <CardHeader>
        <div className="flex justify-between items-start mb-2">
          <Badge
            variant="outline"
            className="px-2 py-0.5 text-xs font-black bg-primary/10 text-primary border-primary/20"
          >
            COM ID: {community.community_id}
          </Badge>
          <div className="flex items-center gap-1 text-xs font-bold text-orange-500">
            <TrendingUp className="h-3 w-3" />
            <span>Avg Impact: {community.avg_impact_score.toFixed(1)}</span>
          </div>
        </div>
        <CardTitle className="text-xl font-black group-hover:text-primary transition-colors">
          Research Cluster {community.community_id}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 space-y-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground font-medium">
          <BookOpen className="h-4 w-4" />
          {community.paper_count} Research Papers
        </div>

        <div className="flex flex-wrap gap-1.5">
          {community.top_topics.slice(0, 4).map((topic) => (
            <Badge
              key={topic}
              variant="secondary"
              className="text-[10px] font-bold px-1.5 py-0 bg-muted/50"
            >
              {topic}
            </Badge>
          ))}
        </div>

        <div className="pt-4 border-t border-muted-foreground/10">
          <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-2">
            Representative Research
          </p>
          <ul className="space-y-2">
            {community.representative_papers.slice(0, 2).map((paper) => (
              <li
                key={paper.paper_id}
                className="text-xs font-medium text-muted-foreground line-clamp-1 flex items-start gap-2"
              >
                <span className="text-primary mt-0.5">▪</span>
                {paper.title}
              </li>
            ))}
          </ul>
        </div>
      </CardContent>

      <CardFooter className="p-0 border-t border-muted-foreground/10 group-hover:bg-primary/5 transition-colors">
        <Button
          variant="ghost"
          className="w-full rounded-none h-12 font-black text-xs gap-2 group-hover:text-primary"
          asChild
        >
          <Link href={`/communities/${community.community_id}`}>
            EXPLORE COMMUNITY
            <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
