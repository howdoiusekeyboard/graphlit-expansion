import type { Metadata } from 'next';
import { JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Footer } from '@/components/layout/Footer';
import { Navbar } from '@/components/layout/Navbar';
import { SessionManager } from '@/components/layout/SessionManager';
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
          <SessionManager />
          <Navbar />
          <main className="flex-1 container px-4 mx-auto py-12">{children}</main>
          <Footer />
        </QueryProvider>
      </body>
    </html>
  );
}
