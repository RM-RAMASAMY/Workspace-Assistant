import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const inlineComponents = {
  p: ({ children }) => <span className="inline">{children}</span>,
  h1: ({ children }) => <span className="block text-2xl font-bold mb-1">{children}</span>,
  h2: ({ children }) => <span className="block text-xl font-semibold mb-1">{children}</span>,
  h3: ({ children }) => <span className="block text-lg font-semibold mb-1">{children}</span>,
  ul: ({ children }) => <span className="block">{children}</span>,
  ol: ({ children }) => <span className="block">{children}</span>,
  li: ({ children }) => <span className="block ml-4 before:content-['•_'] before:text-slate-400">{children}</span>,
  a: ({ href, children }) => (
    <a href={href} className="text-blue-400 underline hover:text-blue-300" target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-slate-800/80 px-1 py-0.5 text-[0.9em] font-mono text-amber-200">{children}</code>
  ),
  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
};

const blockComponents = {
  ...inlineComponents,
  p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
  h1: ({ children }) => <h1 className="mb-3 text-2xl font-bold text-white">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 mt-4 text-xl font-semibold text-white">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-2 mt-3 text-lg font-semibold text-white">{children}</h3>,
  ul: ({ children }) => <ul className="mb-3 list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="mb-3 list-decimal space-y-1 pl-5">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="mb-3 border-l-4 border-slate-600 pl-4 text-slate-300 italic">{children}</blockquote>
  ),
  pre: ({ children }) => (
    <pre className="mb-3 overflow-x-auto rounded-lg bg-slate-950/80 p-3 text-sm font-mono">{children}</pre>
  ),
  code: ({ inline, children }) => (
    inline ? (
      <code className="rounded bg-slate-800/80 px-1 py-0.5 text-[0.9em] font-mono text-amber-200">{children}</code>
    ) : (
      <code className="font-mono text-slate-100">{children}</code>
    )
  ),
  table: ({ children }) => (
    <div className="mb-3 overflow-x-auto">
      <table className="min-w-full border-collapse text-sm">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-slate-700 bg-slate-800 px-3 py-2 text-left font-semibold">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border border-slate-700 px-3 py-2">{children}</td>
  ),
  hr: () => <hr className="my-4 border-slate-700" />,
};

export default function MarkdownContent({ children, inline = false, className = '' }) {
  const text = (children || '').trim();
  if (!text) {
    return null;
  }

  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={inline ? inlineComponents : blockComponents}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
