import type { Metadata } from 'next';
import { Suspense } from 'react';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { SearchPageContent } from '@/components/search/SearchPageContent';

export const metadata: Metadata = {
  title: 'Search Papers',
  description:
    'Discover academic papers by topic, year range, and relevance. Search across 19,917 research papers with AI-powered filtering.',
};

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-12 pb-20">
          <PaperGridSkeleton count={9} />
        </div>
      }
    >
      <SearchPageContent />
    </Suspense>
  );
}
