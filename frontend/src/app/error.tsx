'use client';

import { AlertCircle, RotateCcw } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-8 p-6 text-center">
      <div className="p-8 rounded-[3rem] bg-destructive/10 text-destructive relative">
        <AlertCircle className="h-16 w-16" />
        <div className="absolute inset-0 bg-destructive/20 blur-3xl rounded-full -z-10" />
      </div>

      <div className="space-y-3 max-w-lg">
        <h1 className="text-4xl font-black tracking-tighter uppercase italic leading-none">
          Neural Connection <br />
          <span className="text-destructive">Failure</span>
        </h1>
        <p className="text-muted-foreground font-medium leading-relaxed">
          The research graph encountered a synchronization error. This may be due to an invalid
          paper ID or a momentary system disruption.
        </p>
        {error.digest && (
          <code className="block p-2 text-[10px] font-black bg-muted rounded-lg uppercase tracking-tighter">
            Error Signature: {error.digest}
          </code>
        )}
      </div>

      <div className="flex flex-wrap justify-center gap-4">
        <Button onClick={() => reset()} size="lg" className="rounded-2xl font-black gap-2">
          <RotateCcw className="h-4 w-4" />
          RETRY SYNC
        </Button>
        <Button asChild variant="outline" size="lg" className="rounded-2xl font-black">
          <Link href="/">RETURN TO BASE</Link>
        </Button>
      </div>
    </div>
  );
}
