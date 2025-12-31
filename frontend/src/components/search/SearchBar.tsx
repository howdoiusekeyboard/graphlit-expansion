'use client';

import { Search } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useDebounce } from 'use-debounce';
import { Input } from '@/components/ui/input';

export function SearchBar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [debouncedQuery] = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(debouncedQuery)}`);
    }
  }, [debouncedQuery, router]);

  return (
    <div className="relative w-full max-w-2xl">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        type="search"
        placeholder="Search papers by title, author, or keywords..."
        value={query}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
        className="pl-10 pr-4 py-2 bg-muted/50 focus-visible:bg-background transition-colors"
      />
    </div>
  );
}
