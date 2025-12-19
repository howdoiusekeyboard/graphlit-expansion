'use client';

import { useEffect, useState } from 'react';

export function SessionManager() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    let id = localStorage.getItem('graphlit_session_id');
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem('graphlit_session_id', id);
    }
    setSessionId(id);
  }, []);

  if (process.env.NODE_ENV !== 'development' || !sessionId) {
    return null;
  }

  return (
    <div className="fixed top-2 right-2 z-[100] bg-black/80 text-[10px] text-white px-2 py-1 rounded font-mono border border-white/20 pointer-events-none">
      SID: {sessionId}
    </div>
  );
}
