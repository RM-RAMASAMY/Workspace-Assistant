const CITATION_MARKER_RE = /[\[【]\s*[a-f0-9-]{36}\s*[\]】]|\[\d+\]/gi;

export function stripCitationMarkers(text = '') {
  return text.replace(CITATION_MARKER_RE, '').replace(/\s{2,}/g, ' ').trim();
}

export function formatCitationLabel(citation) {
  const parts = [citation.title || 'Source'];
  if (citation.section_title) {
    parts.push(citation.section_title);
  }
  const lineStart = citation.line_start ?? citation.lineStart;
  const lineEnd = citation.line_end ?? citation.lineEnd;
  if (lineStart && lineEnd) {
    parts.push(`Lines ${lineStart}-${lineEnd}`);
  } else if (lineStart) {
    parts.push(`Line ${lineStart}`);
  } else if (citation.chunk_index != null) {
    parts.push(`Passage ${citation.chunk_index + 1}`);
  }
  return parts.join(' · ');
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
