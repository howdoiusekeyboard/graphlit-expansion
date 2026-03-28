import { ExternalLink } from 'lucide-react';
import Link from 'next/link';
import { API_BASE_URL } from '@/lib/constants';

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
              Graph DBMS-powered citation intelligence platform for discovering thematic clusters
              and predicting research impact through collaborative filtering.
            </p>
            <div className="flex gap-4">
              <Link
                href="https://github.com/howdoiusekeyboard/graphlit-expansion"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg bg-secondary hover:bg-primary hover:text-primary-foreground transition-colors"
                aria-label="View on GitHub"
              >
                <svg viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5" aria-hidden="true">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
                </svg>
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
                  href={`${API_BASE_URL}/docs`}
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
            © 2026 GRAPHLIT INTELLIGENCE SYSTEMS. ALL RIGHTS RESERVED.
          </p>
        </div>
      </div>
    </footer>
  );
}
