import React, { useState } from 'react';
import { X } from 'lucide-react';
import Sidebar from './Sidebar';
import ChatInterface from './ChatInterface';
import DocumentViewer from './DocumentViewer';
import CitationModal from './CitationModal';
import { ChatProvider, useChat } from '../context/ChatContext';

function MainLayoutContent() {
  const [tabs, setTabs] = useState([{ id: 'chat', type: 'chat', title: 'Chat' }]);
  const [activeTabId, setActiveTabId] = useState('chat');
  const [citationModal, setCitationModal] = useState(null);
  const { startNewChat, selectChat, activeSessionId } = useChat();

  const switchTab = (tabId) => {
    if (typeof document !== 'undefined' && document.startViewTransition) {
      document.startViewTransition(() => setActiveTabId(tabId));
      return;
    }
    setActiveTabId(tabId);
  };

  const openDocumentTab = (doc) => {
    setTabs((prev) => {
      const existing = prev.find((tab) => tab.id === doc.id);
      if (existing) {
        return prev.map((tab) =>
          tab.id === doc.id ? { ...tab, highlight: doc.highlight || null } : tab
        );
      }
      return [
        ...prev,
        {
          id: doc.id,
          type: 'document',
          title: doc.title,
          highlight: doc.highlight || null,
        },
      ];
    });
    switchTab(doc.id);
  };

  const openChatTab = (sessionId) => {
    selectChat(sessionId);
    switchTab('chat');
  };

  const handleNewChat = () => {
    startNewChat();
    switchTab('chat');
  };

  const closeTab = (tabId) => {
    setTabs((prev) => {
      const nextTabs = prev.filter((tab) => tab.id !== tabId);
      const resolved = nextTabs.length ? nextTabs : [{ id: 'chat', type: 'chat', title: 'Chat' }];
      if (activeTabId === tabId) {
        const nextId = resolved[resolved.length - 1]?.id || 'chat';
        requestAnimationFrame(() => switchTab(nextId));
      }
      return resolved;
    });
  };

  const activeTab = tabs.find((tab) => tab.id === activeTabId) || tabs[0];
  const documentTabs = tabs.filter((tab) => tab.type === 'document');

  return (
    <div className="flex h-screen bg-slate-900 overflow-hidden">
      <nav aria-label="Application sidebar">
      <Sidebar
        onOpenDocument={openDocumentTab}
        activeDocumentId={activeTab?.type === 'document' ? activeTab.id : null}
        onOpenChat={openChatTab}
        onNewChat={handleNewChat}
        activeSessionId={activeSessionId}
      />
      </nav>

      <main className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-1 overflow-x-auto border-b border-slate-800 bg-slate-950/80 px-2 py-2" role="tablist" aria-label="Open panels">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTabId === tab.id}
              onClick={() => switchTab(tab.id)}
              className={`group inline-flex max-w-xs items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                activeTabId === tab.id
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <span className="truncate">{tab.title}</span>
              {tab.id !== 'chat' && (
                <span
                  onClick={(event) => {
                    event.stopPropagation();
                    closeTab(tab.id);
                  }}
                  className="rounded p-0.5 text-slate-500 hover:bg-slate-700 hover:text-white"
                >
                  <X size={14} />
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="tab-panel relative min-h-0 flex-1">
          <ChatInterface
            onOpenCitation={setCitationModal}
            isVisible={activeTab.type === 'chat'}
          />
          {documentTabs.map((tab) => (
            <div
              key={tab.id}
              className={`absolute inset-0 ${activeTabId === tab.id ? '' : 'hidden'}`}
            >
              <DocumentViewer documentId={tab.id} highlight={tab.highlight} />
            </div>
          ))}
        </div>
      </main>

      {citationModal && (
        <CitationModal
          citation={citationModal}
          onClose={() => setCitationModal(null)}
          onOpenDocument={openDocumentTab}
        />
      )}
    </div>
  );
}

export default function MainLayout() {
  return (
    <ChatProvider>
      <MainLayoutContent />
    </ChatProvider>
  );
}
