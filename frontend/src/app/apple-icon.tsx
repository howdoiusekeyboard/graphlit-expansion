import { ImageResponse } from 'next/og';

export const size = { width: 180, height: 180 };
export const contentType = 'image/png';

export default function AppleIcon() {
  return new ImageResponse(
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #e97316, #ea580c)',
        borderRadius: '40px',
        fontSize: '110px',
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
