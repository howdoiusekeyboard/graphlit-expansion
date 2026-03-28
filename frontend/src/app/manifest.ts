import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'GraphLit ResearchRadar',
    short_name: 'GraphLit',
    description:
      'Citation intelligence platform for academic research discovery through collaborative filtering and community detection.',
    start_url: '/',
    display: 'standalone',
    theme_color: '#e97316',
    background_color: '#0a0a12',
    icons: [{ src: '/favicon.ico', sizes: '16x16 32x32', type: 'image/x-icon' }],
  };
}
