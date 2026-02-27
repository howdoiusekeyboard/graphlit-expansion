'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { BookOpen, LayoutDashboard, Menu, Users, X, Zap } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';

const navLinks = [
  { href: '/communities', label: 'Communities', icon: Users },
  { href: '/feed', label: 'My Feed', icon: LayoutDashboard },
  { href: '/search', label: 'Browse', icon: BookOpen },
] as const;

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  // Close mobile menu on route change
  // biome-ignore lint/correctness/useExhaustiveDependencies: pathname triggers menu close on navigation
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 flex h-16 items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2 font-bold text-xl tracking-tight text-primary"
        >
          <Zap className="h-6 w-6 fill-current" />
          <span>GraphLit</span>
        </Link>

        <div className="hidden md:flex items-center gap-2">
          {navLinks.map((link) => (
            <Button key={link.href} variant="ghost" asChild size="sm">
              <Link href={link.href} className="flex items-center gap-2">
                <link.icon className="h-4 w-4" />
                <span>{link.label}</span>
              </Link>
            </Button>
          ))}
        </div>

        <Button
          variant="ghost"
          size="sm"
          className="md:hidden ml-auto"
          onClick={() => setMobileOpen((prev) => !prev)}
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileOpen}
          aria-controls="mobile-nav"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            id="mobile-nav"
            role="region"
            aria-hidden={!mobileOpen}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden overflow-hidden border-t bg-background/95 backdrop-blur"
          >
            <div className="container py-4 space-y-4">
              <div className="flex flex-col gap-1">
                {navLinks.map((link) => (
                  <Button key={link.href} variant="ghost" asChild className="justify-start">
                    <Link
                      href={link.href}
                      className="flex items-center gap-2"
                      onClick={() => setMobileOpen(false)}
                    >
                      <link.icon className="h-4 w-4" />
                      <span>{link.label}</span>
                    </Link>
                  </Button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
