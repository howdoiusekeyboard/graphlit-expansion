import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils/cn';

interface TopicBadgesProps {
  topics: string[];
  className?: string;
  limit?: number;
  interactive?: boolean;
}

export function TopicBadges({
  topics,
  className,
  limit = 10,
  interactive = true,
}: TopicBadgesProps) {
  const displayTopics = topics.slice(0, limit);

  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {displayTopics.map((topic) =>
        interactive ? (
          <Link key={topic} href={`/search?topics=${encodeURIComponent(topic)}`}>
            <Badge
              variant="secondary"
              className="hover:bg-primary hover:text-primary-foreground transition-colors cursor-pointer font-bold"
            >
              {topic}
            </Badge>
          </Link>
        ) : (
          <Badge key={topic} variant="secondary" className="font-bold">
            {topic}
          </Badge>
        ),
      )}
    </div>
  );
}
