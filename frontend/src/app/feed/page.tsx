import type { Metadata } from 'next';
import FeedClient from './FeedClient';

export const metadata: Metadata = {
  title: 'Research Feed',
  description:
    'Personalized research paper recommendations based on your viewing history and interaction patterns.',
};

export default function FeedPage() {
  return <FeedClient />;
}
