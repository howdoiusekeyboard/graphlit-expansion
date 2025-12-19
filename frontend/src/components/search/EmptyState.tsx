import { SearchX, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  actionHref?: string;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  actionHref,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center space-y-6 rounded-[3rem] border border-dashed bg-muted/5">
      <div className="p-6 rounded-3xl bg-primary/10 text-primary relative">
        <SearchX className="h-12 w-12" />
        <Sparkles className="absolute -top-2 -right-2 h-6 w-6 text-orange-500 animate-pulse" />
      </div>
      <div className="space-y-2 max-w-md">
        <h3 className="text-2xl font-black italic tracking-tight">{title}</h3>
        <p className="text-muted-foreground font-medium leading-relaxed">{description}</p>
      </div>
      {actionLabel && (
        <Button asChild onClick={onAction} size="lg" className="rounded-2xl font-black">
          {actionHref ? <Link href={actionHref}>{actionLabel}</Link> : <span>{actionLabel}</span>}
        </Button>
      )}
    </div>
  );
}
