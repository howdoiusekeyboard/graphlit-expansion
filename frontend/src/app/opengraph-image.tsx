import { ImageResponse } from 'next/og';

export const runtime = 'edge';
export const alt = 'GraphLit ResearchRadar — AI Citation Intelligence';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default function OgImage() {
  return new ImageResponse(
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        width: '100%',
        height: '100%',
        background: 'linear-gradient(135deg, #0a0a12 0%, #1a1a2e 50%, #0a0a12 100%)',
        fontFamily: 'monospace',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '24px',
        }}
      >
        <div
          style={{
            width: '64px',
            height: '64px',
            background: '#e97316',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '36px',
            fontWeight: 900,
            color: 'white',
          }}
        >
          G
        </div>
        <span style={{ fontSize: '48px', fontWeight: 900, color: 'white', letterSpacing: '-2px' }}>
          GraphLit
        </span>
        <span
          style={{ fontSize: '48px', fontWeight: 900, color: '#e97316', letterSpacing: '-2px' }}
        >
          Radar
        </span>
      </div>
      <p
        style={{
          fontSize: '22px',
          color: 'rgba(255,255,255,0.6)',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '4px',
        }}
      >
        AI Citation Intelligence
      </p>
      <p
        style={{
          fontSize: '16px',
          color: 'rgba(255,255,255,0.35)',
          fontWeight: 500,
          marginTop: '16px',
        }}
      >
        19,917 papers · 42 communities · Collaborative filtering · PageRank
      </p>
    </div>,
    { ...size },
  );
}
