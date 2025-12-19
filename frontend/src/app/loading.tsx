import { Loader2, Sparkles } from 'lucide-react';

export default function Loading() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-8">
      <div className="relative">
        <div className="w-24 h-24 rounded-[2rem] bg-primary/10 flex items-center justify-center animate-pulse">
          <Loader2 className="h-12 w-12 text-primary animate-spin" />
        </div>
        <Sparkles className="absolute -top-4 -right-4 h-8 w-8 text-orange-500 animate-bounce" />
      </div>
      <div className="space-y-2 text-center">
        <h2 className="text-2xl font-black uppercase tracking-[0.2em] italic">Initializing</h2>
        <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest animate-pulse">
          Synthesizing Research Graph Data...
        </p>
      </div>
    </div>
  );
}
