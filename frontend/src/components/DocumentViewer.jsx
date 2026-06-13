import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { resolveHighlightRange } from '../utils/citations';
import MarkdownContent from './MarkdownContent';

function normalizeForMatch(text) {
  return (text || '')
    .replace(/^#+\s*/, '')
    .replace(/\*\*/g, '')
    .replace(/__/g, '')
    .replace(/`/g, '')
    .trim()
    .toLowerCase();
}

function findHighlightElement(root, content, lineStart, lineEnd) {
  const lines = content.split('\n');
  const start = Math.max(1, lineStart);
  const end = Math.max(start, lineEnd || start);
  const candidates = lines
    .slice(start - 1, end)
    .map(normalizeForMatch)
    .filter((line) => line.length >= 8);

  const elements = root.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, blockquote, td, th, pre');

  for (const candidate of candidates) {
    for (const el of elements) {
      const elText = normalizeForMatch(el.textContent);
      if (elText.includes(candidate) || candidate.includes(elText.slice(0, Math.min(60, elText.length)))) {
        return el;
      }
    }
  }

  const fallback = normalizeForMatch(lines[start - 1] || '');
  if (fallback.length < 4) {
    return null;
  }
  for (const el of elements) {
    if (normalizeForMatch(el.textContent).includes(fallback)) {
      return el;
    }
  }
  return null;
}

export default function DocumentViewer({ documentId, highlight }) {
  const { token } = useAuth();
  const [document, setDocument] = useState(null);
  const [error, setError] = useState('');
  const contentRef = useRef(null);

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
      return { lineStart: 0, lineEnd: 0, passage: '' };
    }
    return resolveHighlightRange(document.content, highlight || {});
  }, [document, highlight]);

  const { lineStart, lineEnd } = resolvedHighlight;

  useLayoutEffect(() => {
    const root = contentRef.current;
    if (!root || !document?.content) {
      return undefined;
    }

    root.querySelectorAll('.doc-highlight-block').forEach((el) => {
      el.classList.remove('doc-highlight-block');
      el.removeAttribute('id');
    });

    if (lineStart <= 0) {
      return undefined;
    }

    const target = findHighlightElement(root, document.content, lineStart, lineEnd);
    if (!target) {
      return undefined;
    }

    target.id = 'citation-highlight';
    target.classList.add('doc-highlight-block');
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return undefined;
  }, [document, lineStart, lineEnd]);

  if (error) {
    return <div className="flex h-full items-center justify-center text-red-300" role="alert">{error}</div>;
  }

  if (!document) {
    return <div className="flex h-full items-center justify-center text-slate-400" aria-busy="true">Loading document...</div>;
  }

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

      <div ref={contentRef} className="doc-viewer flex-1 overflow-y-auto px-6 py-6">
        <MarkdownContent className="max-w-3xl">{document.content}</MarkdownContent>
      </div>
    </article>
  );
}
