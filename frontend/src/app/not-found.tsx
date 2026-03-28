import { Network } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-8 p-6 text-center">
      <div className="p-8 rounded-[3rem] bg-primary/10 text-primary relative">
        <Network className="h-16 w-16" />
        <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full -z-10" />
      </div>

      <div className="space-y-3 max-w-lg">
        <h1 className="text-4xl font-black tracking-tighter uppercase italic leading-none">
          Research Node <br />
          <span className="text-primary">Not Found</span>
        </h1>
        <p className="text-muted-foreground font-medium leading-relaxed">
          The requested resource does not exist in the citation graph. It may have been removed or
          the URL may be incorrect.
        </p>
      </div>

      <div className="flex flex-wrap justify-center gap-4">
        <Button asChild size="lg" className="rounded-2xl font-black">
          <Link href="/">Return to Base</Link>
        </Button>
        <Button asChild variant="outline" size="lg" className="rounded-2xl font-black">
          <Link href="/communities">Browse Clusters</Link>
        </Button>
      </div>
    </div>
  );
}
