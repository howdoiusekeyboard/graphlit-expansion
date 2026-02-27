import { Suspense } from 'react';
import { PaperGridSkeleton } from '@/components/paper/PaperCardSkeleton';
import { SearchPageContent } from '@/components/search/SearchPageContent';

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
