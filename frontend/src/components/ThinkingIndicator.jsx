import React, { memo } from 'react';

function ThinkingIndicator() {
  return (
    <div
      className="thinking-indicator flex items-center gap-1 py-1"
      role="status"
      aria-label="Assistant is thinking"
    >
      <span className="thinking-dot h-2 w-2 rounded-full bg-slate-400" />
      <span className="thinking-dot h-2 w-2 rounded-full bg-slate-400" />
      <span className="thinking-dot h-2 w-2 rounded-full bg-slate-400" />
    </div>
  );
}

export default memo(ThinkingIndicator);
