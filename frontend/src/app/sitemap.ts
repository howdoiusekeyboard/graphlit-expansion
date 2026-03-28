import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://graphlit.kushagragolash.tech';
  const now = new Date();

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: base, lastModified: now, changeFrequency: 'weekly', priority: 1.0 },
    { url: `${base}/communities`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${base}/search`, lastModified: now, changeFrequency: 'weekly', priority: 0.8 },
    { url: `${base}/feed`, lastModified: now, changeFrequency: 'weekly', priority: 0.7 },
  ];

  const communityRoutes: MetadataRoute.Sitemap = Array.from({ length: 42 }, (_, i) => ({
    url: `${base}/communities/${i}`,
    lastModified: now,
    changeFrequency: 'monthly' as const,
    priority: 0.6,
  }));

  return [...staticRoutes, ...communityRoutes];
}
