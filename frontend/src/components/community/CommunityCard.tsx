'use client';

import { BookOpen, ChevronRight, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import type { CommunityListItem } from '@/lib/utils/validators';

export function CommunityCard({ community }: { community: CommunityListItem }) {
  return (
    <Card className="group hover:shadow-2xl transition-all duration-500 bg-card/50 backdrop-blur-sm border-muted-foreground/10 hover:border-primary/50 flex flex-col h-full overflow-hidden rounded-[2.5rem]">
      <CardHeader className="pb-4">
        <div className="flex justify-between items-start mb-4">
          <Badge
            variant="outline"
            className="px-3 py-1 text-xs font-black bg-primary/10 text-primary border-primary/20 uppercase tracking-widest"
          >
            CLUSTER {community.id}
          </Badge>
          {community.avg_impact !== null && (
            <div className="flex items-center gap-1.5 text-xs font-black text-orange-500 uppercase tracking-tighter">
              <TrendingUp className="h-4 w-4" />
              <span>Impact {community.avg_impact.toFixed(1)}%</span>
            </div>
          )}
        </div>
        <CardTitle className="text-2xl font-black group-hover:text-primary transition-colors tracking-tighter uppercase italic">
          Research Cluster {community.id}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 space-y-6">
        <div className="flex items-center gap-3 text-sm text-muted-foreground font-bold uppercase tracking-widest">
          <BookOpen className="h-5 w-5 text-primary" />
          {community.paper_count} Knowledge Nodes
        </div>

        <div className="space-y-3">
          <p className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em]">
            Primary Thematic Anchors
          </p>
          <div className="flex flex-wrap gap-2">
            {community.top_topics.map((topic) => (
              <Badge
                key={topic}
                variant="secondary"
                className="text-[10px] font-bold px-2 py-0.5 bg-muted/50 border border-muted-foreground/5"
              >
                {topic}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>

      <CardFooter className="p-0 border-t border-muted-foreground/10 group-hover:bg-primary/5 transition-colors">
        <Button
          variant="ghost"
          className="w-full rounded-none h-14 font-black text-xs gap-3 group-hover:text-primary uppercase tracking-[0.2em]"
          asChild
        >
          <Link href={`/communities/${community.id}`}>
            Analyze Topology
            <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-2" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
