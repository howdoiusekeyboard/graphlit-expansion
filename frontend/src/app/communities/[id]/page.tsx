import type { Metadata } from 'next';
import CommunityDetailClient from './CommunityDetailClient';

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return {
    title: `Research Cluster ${id}`,
    description: `Explore trending papers, citation network topology, and thematic analytics for research cluster ${id}.`,
  };
}

export default async function CommunityDetailPage({ params }: Props) {
  const { id } = await params;
  return <CommunityDetailClient communityId={parseInt(id, 10)} />;
}
