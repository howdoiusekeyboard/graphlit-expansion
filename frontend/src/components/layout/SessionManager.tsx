'use client';

import { useState } from 'react';

function getOrCreateSessionId(): string | null {
  if (typeof window === 'undefined') return null;
  let id = localStorage.getItem('graphlit_session_id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('graphlit_session_id', id);
  }
  return id;
}

export function SessionManager() {
  const [sessionId] = useState(getOrCreateSessionId);

  if (process.env.NODE_ENV !== 'development' || !sessionId) {
    return null;
  }

  return (
    <div className="fixed bottom-2 right-2 z-[100] bg-black/80 text-[10px] text-white/50 px-2 py-1 rounded font-mono border border-white/10 pointer-events-none opacity-30">
      SID: {sessionId}
    </div>
  );
}
