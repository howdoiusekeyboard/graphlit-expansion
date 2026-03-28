import type { Metadata } from 'next';
import CommunitiesClient from './CommunitiesClient';

export const metadata: Metadata = {
  title: 'Research Communities',
  description:
    'Browse 42 research clusters detected via Louvain community detection on the citation network. Ranked by impact score and paper count.',
};

export default function CommunitiesPage() {
  return <CommunitiesClient />;
}
