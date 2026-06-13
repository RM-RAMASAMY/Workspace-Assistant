const CITATION_MARKER_RE = /[\[【]\s*[a-f0-9-]{36}\s*[\]】]|\[\d+\]/gi;

/** Remove citation markers; preserve newlines for markdown rendering. */
export function stripCitationMarkers(text = '') {
  return (text || '')
    .replace(CITATION_MARKER_RE, '')
    .replace(/[^\S\n]{2,}/g, ' ')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

/** Normalize streamed LLM text so common list patterns render as markdown lists. */
export function prepareAssistantMarkdown(text = '') {
  let cleaned = stripCitationMarkers(text);
  cleaned = cleaned.replace(/:\s+-\s+/g, ':\n\n- ');
  cleaned = cleaned.replace(/([.!?])\s+-\s+\*\*/g, '$1\n\n- **');
  cleaned = cleaned.replace(/([.!?])\s+-\s+/g, '$1\n\n- ');
  cleaned = cleaned.replace(/\n-\s+/g, '\n- ');
  return cleaned;
}

export function formatDocumentTitle(title) {
  if (!title) {
    return 'Source';
  }
  let name = title.replace(/\.md$/i, '');
  if (name.startsWith('hanuinnotech_')) {
    name = name.slice('hanuinnotech_'.length);
  }
  return name
    .split('_')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function formatCitationLocation(citation) {
  const lineStart = citation.line_start ?? citation.lineStart;
  const lineEnd = citation.line_end ?? citation.lineEnd;
  if (lineStart > 0) {
    if (lineEnd > lineStart) {
      return `Lines ${lineStart}–${lineEnd}`;
    }
    return `Line ${lineStart}`;
  }
  return null;
}

export function formatCitationExcerpt(citation, maxLen = 72) {
  const text = (citation?.text || '').replace(/\s+/g, ' ').trim();
  if (!text) {
    return null;
  }
  if (text.length <= maxLen) {
    return text;
  }
  return `${text.slice(0, maxLen).trim()}…`;
}

export function formatCitationLabel(citation) {
  const parts = [formatDocumentTitle(citation.title)];
  if (citation.section_title) {
    parts.push(citation.section_title);
  }
  const location = formatCitationLocation(citation);
  if (location) {
    parts.push(location);
  }
  return parts.join(' · ');
}

export function formatCitationParts(citation) {
  const docTitle = formatDocumentTitle(citation.title);
  const section = citation.section_title || null;
  const location = formatCitationLocation(citation);
  const excerpt = !location ? formatCitationExcerpt(citation) : null;
  return { docTitle, section, location, excerpt };
}

export function dedupeCitations(citations = []) {
  const seen = new Set();
  return citations.filter((citation) => {
    if (!citation?.id || seen.has(citation.id)) {
      return false;
    }
    seen.add(citation.id);
    return true;
  });
}

/** Map citation metadata to document line range; falls back to passage text search. */
export function resolveHighlightRange(content, citation) {
  const lineStart = citation?.line_start ?? citation?.lineStart ?? 0;
  const lineEnd = citation?.line_end ?? citation?.lineEnd ?? 0;
  if (lineStart > 0) {
    return {
      lineStart,
      lineEnd: lineEnd > 0 ? lineEnd : lineStart,
      passage: citation?.text || '',
    };
  }

  const passage = (citation?.text || '').trim();
  if (!passage || !content) {
    return { lineStart: 0, lineEnd: 0, passage: '' };
  }

  const candidates = [
    passage.slice(0, 200).trim(),
    passage.split('\n').find((line) => line.trim().length > 24)?.trim(),
    passage.slice(0, 80).trim(),
  ].filter(Boolean);

  for (const snippet of candidates) {
    const idx = content.indexOf(snippet);
    if (idx < 0) {
      continue;
    }
    const before = content.slice(0, idx);
    const start = before.split('\n').length;
    const spanLines = snippet.split('\n').length;
    return {
      lineStart: start,
      lineEnd: start + spanLines - 1,
      passage: snippet,
    };
  }

  return { lineStart: 0, lineEnd: 0, passage };
}

export function findLastAssistantIndex(messages) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i]?.role === 'assistant') {
      return i;
    }
  }
  return -1;
}
