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
  metadataBase: new URL('https://graphlit.kushagragolash.tech'),
  title: {
    default: 'GraphLit ResearchRadar | AI Citation Intelligence',
    template: '%s | GraphLit ResearchRadar',
  },
  description:
    'Citation intelligence platform for academic research discovery through collaborative filtering and community detection.',
  openGraph: {
    type: 'website',
    siteName: 'GraphLit ResearchRadar',
    locale: 'en_US',
  },
  twitter: { card: 'summary_large_image' },
  manifest: '/manifest.webmanifest',
  other: { 'theme-color': '#e97316' },
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
        <script
          type="application/ld+json"
          // biome-ignore lint/security/noDangerouslySetInnerHtml: JSON-LD structured data is hardcoded, not user input
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'WebApplication',
              name: 'GraphLit ResearchRadar',
              url: 'https://graphlit.kushagragolash.tech',
              applicationCategory: 'ResearchTool',
              description:
                'Citation intelligence platform for academic research discovery through collaborative filtering and community detection.',
              author: {
                '@type': 'Person',
                name: 'Kushagra Golash',
                url: 'https://kushagragolash.tech',
              },
            }),
          }}
        />
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
