import React, { memo } from 'react';
import { FileText } from 'lucide-react';
import { formatCitationParts } from '../utils/citations';

function CitationChip({ citation, onClick }) {
  const { docTitle, section, location, excerpt } = formatCitationParts(citation);
  const meta = [section, location || excerpt].filter(Boolean).join(' · ');

  return (
    <button
      type="button"
      onClick={onClick}
      className="citation-chip group flex max-w-full items-start gap-2.5 rounded-lg border border-slate-700/80 bg-slate-950/50 px-3 py-2.5 text-left transition-colors hover:border-amber-500/40 hover:bg-slate-900/80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-400"
      title="View source excerpt"
    >
      <FileText
        size={16}
        className="mt-0.5 shrink-0 text-amber-400/90 group-hover:text-amber-300"
        aria-hidden="true"
      />
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium text-slate-100">{docTitle}</span>
        {meta && (
          <span className="mt-0.5 block text-xs leading-snug text-slate-400 group-hover:text-slate-300">
            {meta}
          </span>
        )}
      </span>
    </button>
  );
}

export default memo(CitationChip);
