import type { Metadata } from 'next';
import { API_BASE_URL } from '@/lib/constants';
import PaperDetailClient from './PaperDetailClient';

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/paper/${id}/detail`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return { title: `Paper ${id}` };
    const paper = await res.json();
    return {
      title: paper.title,
      description:
        paper.abstract?.slice(0, 160) ||
        `Research paper ${id} — citation network analysis and impact scoring.`,
    };
  } catch {
    return { title: `Paper ${id}` };
  }
}

export default async function PaperDetailPage({ params }: Props) {
  const { id } = await params;
  return <PaperDetailClient paperId={id} />;
}
