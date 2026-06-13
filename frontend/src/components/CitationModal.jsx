import React, { useEffect, useRef, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { formatCitationParts, resolveHighlightRange } from '../utils/citations';
import MarkdownContent from './MarkdownContent';

export default function CitationModal({ citation, onClose, onOpenDocument }) {
  const { token } = useAuth();
  const [detail, setDetail] = useState(citation);
  const [loading, setLoading] = useState(true);
  const dialogRef = useRef(null);
  const closeButtonRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return undefined;
    }
    if (!dialog.open) {
      dialog.showModal();
    }
    closeButtonRef.current?.focus();

    const handleCancel = (event) => {
      event.preventDefault();
      onClose();
    };
    dialog.addEventListener('cancel', handleCancel);
    return () => dialog.removeEventListener('cancel', handleCancel);
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await apiCall(`/documents/chunks/${citation.id}`, 'GET', null, token);
        if (!cancelled) {
          setDetail(data);
        }
      } catch (err) {
        console.error(err);
        if (!cancelled) {
          setDetail(citation);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [citation, token]);

  const handleClose = () => {
    dialogRef.current?.close();
    onClose();
  };

  const handleOpenDocument = async () => {
    let content = '';
    try {
      const doc = await apiCall(`/documents/${detail.document_id}/content`, 'GET', null, token);
      content = doc.content || '';
    } catch {
      // Fall back to line metadata only.
    }

    const resolved = resolveHighlightRange(content, detail);
    onOpenDocument({
      id: detail.document_id,
      title: detail.title,
      highlight: resolved,
    });
    handleClose();
  };

  const { docTitle, section, location, excerpt } = formatCitationParts(detail);
  const meta = [section, location || excerpt].filter(Boolean).join(' · ');

  return (
    <dialog
      ref={dialogRef}
      className="citation-dialog glass-panel max-h-[80vh] w-[min(42rem,92vw)] overflow-hidden rounded-2xl border border-slate-700/60 p-0 text-slate-100 backdrop:bg-black/60"
      aria-labelledby="citation-title"
    >
      <div className="flex items-start justify-between border-b border-slate-700/60 px-5 py-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">Source excerpt</p>
          <h3 id="citation-title" className="mt-1 text-lg font-medium text-white">
            {docTitle}
          </h3>
          {meta && (
            <p className="mt-1 text-sm text-slate-400">{meta}</p>
          )}
        </div>
        <button
          ref={closeButtonRef}
          type="button"
          onClick={handleClose}
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400"
          aria-label="Close source dialog"
        >
          ✕
        </button>
      </div>

      <div className="max-h-[50vh] overflow-y-auto px-5 py-4">
        {loading ? (
          <p className="text-sm text-slate-400" aria-live="polite">Loading source...</p>
        ) : (
          <blockquote className="rounded-xl border border-amber-500/30 bg-slate-950/70 p-4 text-sm">
            <MarkdownContent>{detail.text}</MarkdownContent>
          </blockquote>
        )}
      </div>

      <div className="flex justify-end gap-2 border-t border-slate-700/60 px-5 py-4">
        <button
          type="button"
          onClick={handleOpenDocument}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-300"
        >
          <ExternalLink size={16} aria-hidden="true" />
          Open full document
        </button>
      </div>
    </dialog>
  );
}
