import type { Metadata } from 'next';
import { JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Navbar } from '@/components/layout/Navbar';
import { QueryProvider } from '@/components/providers/QueryProvider';

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
});

export const metadata: Metadata = {
  title: 'GraphLit ResearchRadar | AI Citation Intelligence',
  description: 'AI-powered citation intelligence and academic research discovery platform.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${jetbrainsMono.variable} font-mono antialiased min-h-screen flex flex-col`}
      >
        <QueryProvider>
          <Navbar />
          <main className="flex-1 container py-8">{children}</main>
          <footer className="border-t py-6 bg-muted/20">
            <div className="container text-center text-sm text-muted-foreground">
              <p>
                © 2025 GraphLit ResearchRadar. Powered by OpenAlex & Louvain Community Detection.
              </p>
            </div>
          </footer>
        </QueryProvider>
      </body>
    </html>
  );
}
