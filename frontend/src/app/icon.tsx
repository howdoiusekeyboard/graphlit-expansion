import { ImageResponse } from 'next/og';

export const size = { width: 32, height: 32 };
export const contentType = 'image/png';

export default function Icon() {
  return new ImageResponse(
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#e97316',
        borderRadius: '6px',
        fontSize: '20px',
        fontWeight: 900,
        color: 'white',
        fontFamily: 'monospace',
      }}
    >
      G
    </div>,
    { ...size },
  );
}
