'use client';

import { BookOpen, LayoutDashboard, Users, Zap } from 'lucide-react';
import Link from 'next/link';
import { SearchBar } from '@/components/search/SearchBar';
import { Button } from '@/components/ui/button';

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center gap-4">
        <Link
          href="/"
          className="flex items-center gap-2 font-bold text-xl tracking-tight text-primary"
        >
          <Zap className="h-6 w-6 fill-current" />
          <span>GraphLit</span>
        </Link>

        <div className="flex-1 flex justify-center max-w-xl mx-auto">
          <SearchBar />
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" asChild size="sm">
            <Link href="/communities" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              <span>Communities</span>
            </Link>
          </Button>
          <Button variant="ghost" asChild size="sm">
            <Link href="/feed" className="flex items-center gap-2">
              <LayoutDashboard className="h-4 w-4" />
              <span>My Feed</span>
            </Link>
          </Button>
          <Button variant="ghost" asChild size="sm">
            <Link href="/search" className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              <span>Browse</span>
            </Link>
          </Button>
        </div>
      </div>
    </nav>
  );
}
