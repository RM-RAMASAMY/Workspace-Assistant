import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { resolveHighlightRange } from '../utils/citations';
import MarkdownContent from './MarkdownContent';

export default function DocumentViewer({ documentId, highlight }) {
  const { token } = useAuth();
  const [document, setDocument] = useState(null);
  const [error, setError] = useState('');
  const highlightRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setError('');
      try {
        const data = await apiCall(`/documents/${documentId}/content`, 'GET', null, token);
        if (!cancelled) {
          setDocument(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load document');
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [documentId, token]);

  const resolvedHighlight = useMemo(() => {
    if (!document?.content) {
      return { lineStart: 0, lineEnd: 0 };
    }
    return resolveHighlightRange(document.content, highlight || {});
  }, [document, highlight]);

  const { lineStart, lineEnd } = resolvedHighlight;

  useEffect(() => {
    if (highlightRef.current) {
      highlightRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [document, lineStart, lineEnd]);

  if (error) {
    return <div className="flex h-full items-center justify-center text-red-300" role="alert">{error}</div>;
  }

  if (!document) {
    return <div className="flex h-full items-center justify-center text-slate-400" aria-busy="true">Loading document...</div>;
  }

  const lines = document.content.split('\n');

  return (
    <article className="flex h-full flex-col bg-slate-900">
      <header className="border-b border-slate-800 px-6 py-4">
        <h2 className="text-lg font-medium text-white">{document.title}</h2>
        {lineStart > 0 && (
          <p className="mt-1 text-sm text-amber-300">
            Highlighting lines {lineStart}
            {lineEnd > lineStart ? `–${lineEnd}` : ''}
          </p>
        )}
        {lineStart === 0 && highlight?.passage && (
          <p className="mt-1 text-sm text-slate-400">Source passage could not be mapped to exact line numbers.</p>
        )}
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        <pre className="rounded-xl border border-slate-800 bg-slate-950/50 font-mono text-sm">
          {lines.map((line, index) => {
            const lineNumber = index + 1;
            const isHighlighted = lineStart > 0
              && lineNumber >= lineStart
              && lineNumber <= (lineEnd || lineStart);

            return (
              <div
                key={`${documentId}-${lineNumber}`}
                ref={isHighlighted && lineNumber === lineStart ? highlightRef : null}
                className={`grid grid-cols-[4rem_1fr] gap-4 px-4 py-1 ${
                  isHighlighted ? 'bg-amber-500/15 border-l-2 border-amber-400' : ''
                }`}
              >
                <span className="select-none text-right text-slate-500" aria-hidden="true">{lineNumber}</span>
                <span className="text-slate-100">
                  {line ? <MarkdownContent inline>{line}</MarkdownContent> : ' '}
                </span>
              </div>
            );
          })}
        </pre>
      </div>
    </article>
  );
}
