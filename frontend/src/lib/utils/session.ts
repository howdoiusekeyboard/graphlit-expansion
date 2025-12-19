export function getOrCreateSessionId(): string {
  if (typeof window === 'undefined') return '';

  let sessionId = localStorage.getItem('graphlit_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('graphlit_session_id', sessionId);
  }
  return sessionId;
}
