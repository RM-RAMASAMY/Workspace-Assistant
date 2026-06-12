import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useAuth } from './AuthContext';

const ChatContext = createContext(null);

function storageKey(userId) {
  return `voice-rag-chats-${userId || 'anonymous'}`;
}

function createSession(title = 'New chat') {
  const now = new Date().toISOString();
  return {
    id: crypto.randomUUID(),
    title,
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
}

function deriveTitle(messages) {
  const firstUser = messages.find((msg) => msg.role === 'user');
  if (!firstUser?.content) {
    return 'New chat';
  }
  const text = firstUser.content.trim();
  return text.length > 42 ? `${text.slice(0, 42)}…` : text;
}

export function ChatProvider({ children }) {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const key = storageKey(user?.id);
    try {
      const raw = localStorage.getItem(key);
      if (raw) {
        const parsed = JSON.parse(raw);
        setSessions(parsed.sessions || []);
        setActiveSessionId(parsed.activeSessionId || parsed.sessions?.[0]?.id || null);
      } else {
        const initial = createSession();
        setSessions([initial]);
        setActiveSessionId(initial.id);
      }
    } catch {
      const initial = createSession();
      setSessions([initial]);
      setActiveSessionId(initial.id);
    }
    setHydrated(true);
  }, [user?.id]);

  useEffect(() => {
    if (!hydrated || !user?.id) {
      return;
    }
    localStorage.setItem(
      storageKey(user.id),
      JSON.stringify({ sessions, activeSessionId })
    );
  }, [sessions, activeSessionId, hydrated, user?.id]);

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) || sessions[0],
    [sessions, activeSessionId]
  );

  const updateActiveMessages = useCallback((updater) => {
    setSessions((prev) =>
      prev.map((session) => {
        if (session.id !== activeSessionId) {
          return session;
        }
        const messages = typeof updater === 'function' ? updater(session.messages) : updater;
        return {
          ...session,
          messages,
          title: deriveTitle(messages),
          updatedAt: new Date().toISOString(),
        };
      })
    );
  }, [activeSessionId]);

  const startNewChat = useCallback(() => {
    const session = createSession();
    setSessions((prev) => [session, ...prev]);
    setActiveSessionId(session.id);
    return session.id;
  }, [activeSessionId]);

  const selectChat = useCallback((sessionId) => {
    setActiveSessionId(sessionId);
  }, []);

  const deleteChat = useCallback((sessionId) => {
    setSessions((prev) => {
      const next = prev.filter((session) => session.id !== sessionId);
      if (next.length === 0) {
        const fresh = createSession();
        setActiveSessionId(fresh.id);
        return [fresh];
      }
      if (activeSessionId === sessionId) {
        setActiveSessionId(next[0].id);
      }
      return next;
    });
  }, [activeSessionId]);

  const value = useMemo(() => ({
    sessions,
    activeSession,
    activeSessionId,
    hydrated,
    updateActiveMessages,
    startNewChat,
    selectChat,
    deleteChat,
  }), [
    sessions,
    activeSession,
    activeSessionId,
    hydrated,
    updateActiveMessages,
    startNewChat,
    selectChat,
    deleteChat,
  ]);

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within ChatProvider');
  }
  return context;
}
