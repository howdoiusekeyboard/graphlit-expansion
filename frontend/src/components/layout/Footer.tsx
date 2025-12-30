import { ExternalLink, Github } from 'lucide-react';
import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t bg-card/50 backdrop-blur-md py-12">
      <div className="container px-4 mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          <div className="col-span-1 md:col-span-2 space-y-6">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center transition-transform group-hover:rotate-12">
                <span className="text-primary-foreground font-black text-xl italic">G</span>
              </div>
              <span className="text-2xl font-black tracking-tighter uppercase">
                GraphLit <span className="text-primary">Radar</span>
              </span>
            </Link>
            <p className="text-muted-foreground font-medium max-w-sm leading-relaxed">
              AI-powered citation intelligence platform for discovering thematic clusters and
              predicting research impact through collaborative filtering.
            </p>
            <div className="flex gap-4">
              <Link
                href="https://github.com/howdoiusekeyboard/graphlit-expansion"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg bg-secondary hover:bg-primary hover:text-primary-foreground transition-colors"
                aria-label="View on GitHub"
              >
                <Github className="h-5 w-5" />
              </Link>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="font-black text-sm uppercase tracking-widest">Platform</h4>
            <ul className="space-y-2 text-sm font-bold text-muted-foreground">
              <li>
                <Link href="/search" className="hover:text-primary transition-colors">
                  Search Discovery
                </Link>
              </li>
              <li>
                <Link href="/communities" className="hover:text-primary transition-colors">
                  Research Clusters
                </Link>
              </li>
              <li>
                <Link href="/feed" className="hover:text-primary transition-colors">
                  Neural Feed
                </Link>
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h4 className="font-black text-sm uppercase tracking-widest">Resources</h4>
            <ul className="space-y-2 text-sm font-bold text-muted-foreground">
              <li>
                <Link
                  href="http://localhost:8080/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-primary transition-colors inline-flex items-center gap-1"
                >
                  API Documentation
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </li>
              <li>
                <Link
                  href="https://openalex.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-primary transition-colors inline-flex items-center gap-1"
                >
                  OpenAlex Dataset
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </li>
              <li>
                <Link
                  href="https://en.wikipedia.org/wiki/Louvain_method"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-primary transition-colors inline-flex items-center gap-1"
                >
                  Louvain Algorithm
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t text-center">
          <p className="text-xs font-black uppercase tracking-tighter text-muted-foreground">
            © 2025 GRAPHLIT INTELLIGENCE SYSTEMS. ALL RIGHTS RESERVED.
          </p>
        </div>
      </div>
    </footer>
  );
}
