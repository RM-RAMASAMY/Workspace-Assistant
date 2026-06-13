import React, { useState, useEffect, useRef, useCallback, memo } from 'react';
import PushToTalk from './PushToTalk';
import { useChat } from '../context/ChatContext';
import {
  stripCitationMarkers,
  prepareAssistantMarkdown,
  dedupeCitations,
  findLastAssistantIndex,
} from '../utils/citations';
import MarkdownContent from './MarkdownContent';
import CitationChip from './CitationChip';
import ThinkingIndicator from './ThinkingIndicator';

const EMPTY_ASSISTANT_FALLBACK =
  "I couldn't generate a response for that question. Please try rephrasing or ask again.";

const ChatMessage = memo(function ChatMessage({ msg, onOpenCitation }) {
  const assistantText = msg.role === 'assistant'
    ? prepareAssistantMarkdown(msg.content)
    : '';
  const isThinking = msg.role === 'assistant' && msg.thinking && !assistantText;

  if (msg.role === 'assistant' && !assistantText && !isThinking && !(msg.citations?.length)) {
    return null;
  }

  return (
    <div className={`flex ${msg.role === 'user' ? 'justify-end' : msg.role === 'system' ? 'justify-center' : 'justify-start'}`}>
      <div className={`max-w-2xl rounded-2xl px-6 py-4 ${
        msg.role === 'user' ? 'bg-blue-600 text-white' :
        msg.role === 'system' ? 'bg-amber-900/40 text-amber-200 border border-amber-700/40 text-sm' :
        'glass-panel text-slate-100'
      }`}>
        {isThinking ? (
          <ThinkingIndicator />
        ) : msg.role === 'assistant' ? (
          <MarkdownContent>{assistantText}</MarkdownContent>
        ) : (
          <p className="leading-relaxed whitespace-pre-wrap">{stripCitationMarkers(msg.content)}</p>
        )}

        {msg.citations && msg.citations.length > 0 && (
          <div className="mt-4 border-t border-slate-700/50 pt-4">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Sources</p>
            <div className="flex flex-col gap-2">
              {dedupeCitations(msg.citations).map((cit) => (
                <CitationChip
                  key={cit.id}
                  citation={cit}
                  onClick={() => onOpenCitation?.(cit)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

export default function ChatInterface({ onOpenCitation, isVisible }) {
  const { activeSession, activeSessionId, hydrated, updateActiveMessages } = useChat();
  const messages = activeSession?.messages || [];
  const [isProcessing, setIsProcessing] = useState(false);
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const currentTextRef = useRef('');
  const audioQueueRef = useRef([]);
  const isPlayingAudioRef = useRef(false);
  const currentSourceRef = useRef(null);
  const sessionIdRef = useRef(activeSessionId);
  const processingTimeoutRef = useRef(null);
  const updateMessagesRef = useRef(updateActiveMessages);
  const isProcessingRef = useRef(false);
  const textFlushRafRef = useRef(null);
  const activeAssistantTurnRef = useRef(false);
  const messagesRef = useRef(messages);

  updateMessagesRef.current = updateActiveMessages;
  messagesRef.current = messages;

  const buildHistoryPayload = useCallback(() => (
    messagesRef.current
      .filter((msg) => (msg.role === 'user' || msg.role === 'assistant') && msg.content?.trim())
      .slice(-12)
      .map((msg) => ({
        role: msg.role,
        content: stripCitationMarkers(msg.content).slice(0, 1000),
      }))
  ), []);

  const flushStreamingText = useCallback((sessionId) => {
    if (!activeAssistantTurnRef.current) {
      return;
    }
    if (textFlushRafRef.current) {
      cancelAnimationFrame(textFlushRafRef.current);
      textFlushRafRef.current = null;
    }
    const content = prepareAssistantMarkdown(currentTextRef.current);
    updateMessagesRef.current((prev) => {
      if (sessionIdRef.current !== sessionId) {
        return prev;
      }
      const newMsgs = [...prev];
      const idx = findLastAssistantIndex(newMsgs);
      if (idx >= 0) {
        newMsgs[idx] = { ...newMsgs[idx], content, thinking: false };
      }
      return newMsgs;
    });
  }, []);

  const scheduleStreamingTextFlush = useCallback((sessionId) => {
    if (textFlushRafRef.current) {
      return;
    }
    textFlushRafRef.current = requestAnimationFrame(() => {
      textFlushRafRef.current = null;
      flushStreamingText(sessionId);
    });
  }, [flushStreamingText]);

  useEffect(() => {
    sessionIdRef.current = activeSessionId;
    currentTextRef.current = '';
    activeAssistantTurnRef.current = false;
    setIsProcessing(false);
    isProcessingRef.current = false;
  }, [activeSessionId]);

  useEffect(() => {
    isProcessingRef.current = isProcessing;
  }, [isProcessing]);

  const stopProcessing = useCallback(() => {
    isProcessingRef.current = false;
    setIsProcessing(false);
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }
  }, []);

  const startProcessing = useCallback(() => {
    isProcessingRef.current = true;
    setIsProcessing(true);
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
    }
    processingTimeoutRef.current = setTimeout(() => {
      stopProcessing();
      updateMessagesRef.current((prev) => [
        ...prev,
        {
          role: 'system',
          content: 'Request timed out. Please try again.',
          citations: [],
        },
      ]);
    }, 60000);
  }, [stopProcessing]);

  useEffect(() => {
    if (!hydrated) {
      return undefined;
    }

    let cancelled = false;
    let reconnectTimer = null;

    const connect = () => {
      if (cancelled) {
        return;
      }

      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = import.meta.env.VITE_WS_URL
        || `${wsProtocol}//${window.location.host}/voice/ws`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => console.log('WebSocket connected');

      ws.onclose = () => {
        if (cancelled) {
          return;
        }
        if (isProcessingRef.current) {
          stopProcessing();
          updateMessagesRef.current((prev) => [
            ...prev,
            {
              role: 'system',
              content: 'Connection lost during processing. Reconnecting — please try again.',
              citations: [],
            },
          ]);
        }
        reconnectTimer = setTimeout(connect, 1500);
      };

      ws.onerror = () => {
        if (isProcessingRef.current) {
          stopProcessing();
        }
      };

      ws.onmessage = async (event) => {
        const msg = JSON.parse(event.data);
        const sessionId = sessionIdRef.current;

        const patchMessages = (updater) => {
          updateMessagesRef.current((prev) => {
            if (sessionIdRef.current !== sessionId) {
              return prev;
            }
            return typeof updater === 'function' ? updater(prev) : updater;
          });
        };

        if (msg.type === 'status') {
          if (msg.data === 'Done') {
            if (activeAssistantTurnRef.current) {
              flushStreamingText(sessionId);
              patchMessages((prev) => {
                const newMsgs = [...prev];
                const idx = findLastAssistantIndex(newMsgs);
                if (idx >= 0 && !newMsgs[idx].content?.trim()) {
                  newMsgs[idx] = {
                    ...newMsgs[idx],
                    content: EMPTY_ASSISTANT_FALLBACK,
                    thinking: false,
                  };
                }
                return newMsgs;
              });
            }
            activeAssistantTurnRef.current = false;
            stopProcessing();
            currentTextRef.current = '';
          }
        } else if (msg.type === 'transcription') {
          stopAudioPlayback();
          activeAssistantTurnRef.current = true;
          currentTextRef.current = '';
          patchMessages((prev) => [
            ...prev,
            { role: 'user', content: msg.data },
            { role: 'assistant', content: '', citations: [], thinking: true },
          ]);
        } else if (msg.type === 'text') {
          if (isProcessingRef.current) {
            stopProcessing();
          }
          currentTextRef.current += `${msg.data} `;
          updateMessagesRef.current((prev) => {
            if (sessionIdRef.current !== sessionId) {
              return prev;
            }
            const newMsgs = [...prev];
            const idx = findLastAssistantIndex(newMsgs);
            if (idx >= 0) {
              newMsgs[idx] = { ...newMsgs[idx], thinking: false };
            }
            return newMsgs;
          });
          scheduleStreamingTextFlush(sessionId);
        } else if (msg.type === 'citations') {
          flushStreamingText(sessionId);
          patchMessages((prev) => {
            const newMsgs = [...prev];
            const idx = findLastAssistantIndex(newMsgs);
            if (idx >= 0) {
              newMsgs[idx] = {
                ...newMsgs[idx],
                citations: msg.data || [],
              };
            }
            return newMsgs;
          });
        } else if (msg.type === 'audio') {
          enqueueAudio(msg.data);
        } else if (msg.type === 'error') {
          console.error('WS Error:', msg.data);
          currentTextRef.current = '';
          if (activeAssistantTurnRef.current) {
            patchMessages((prev) => {
              const newMsgs = [...prev];
              const idx = findLastAssistantIndex(newMsgs);
              if (idx >= 0 && !newMsgs[idx].content?.trim()) {
                newMsgs[idx] = { ...newMsgs[idx], content: msg.data, thinking: false };
                return newMsgs;
              }
              return [...prev, { role: 'system', content: msg.data, citations: [] }];
            });
          } else {
            patchMessages((prev) => [
              ...prev,
              { role: 'system', content: msg.data, citations: [] },
            ]);
          }
          activeAssistantTurnRef.current = false;
          stopProcessing();
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [hydrated, stopProcessing, flushStreamingText, scheduleStreamingTextFlush]);

  const stopAudioPlayback = () => {
    audioQueueRef.current = [];
    isPlayingAudioRef.current = false;
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop();
      } catch {
        // Already stopped.
      }
      currentSourceRef.current = null;
    }
  };

  const enqueueAudio = (base64Data) => {
    audioQueueRef.current.push(base64Data);
    if (!isPlayingAudioRef.current) {
      drainAudioQueue();
    }
  };

  const drainAudioQueue = async () => {
    if (isPlayingAudioRef.current || audioQueueRef.current.length === 0) {
      return;
    }

    isPlayingAudioRef.current = true;

    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume();
    }

    while (audioQueueRef.current.length > 0) {
      const base64Data = audioQueueRef.current.shift();
      try {
        const binaryStr = window.atob(base64Data);
        const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) {
          bytes[i] = binaryStr.charCodeAt(i);
        }
        const audioData = await audioContextRef.current.decodeAudioData(bytes.buffer.slice(0));
        await new Promise((resolve) => {
          const source = audioContextRef.current.createBufferSource();
          source.buffer = audioData;
          source.connect(audioContextRef.current.destination);
          currentSourceRef.current = source;
          source.onended = () => {
            if (currentSourceRef.current === source) {
              currentSourceRef.current = null;
            }
            resolve();
          };
          source.start(0);
        });
      } catch (err) {
        console.error('Audio playback failed:', err);
      }
    }

    isPlayingAudioRef.current = false;
  };

  const handleAudioComplete = useCallback((audioBlob) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      stopAudioPlayback();
      startProcessing();
      ws.send(JSON.stringify({ type: 'turn', history: buildHistoryPayload() }));
      ws.send(audioBlob);
    } else {
      stopProcessing();
      updateMessagesRef.current((prev) => [
        ...prev,
        {
          role: 'system',
          content: 'Not connected yet. Wait a moment and try again.',
          citations: [],
        },
      ]);
    }
  }, [startProcessing, stopProcessing, buildHistoryPayload]);

  if (!hydrated) {
    return (
      <div className="flex h-full items-center justify-center text-slate-400">
        Loading chat...
      </div>
    );
  }

  return (
    <div className={`flex h-full flex-col bg-slate-900 relative ${isVisible ? '' : 'hidden'}`}>
      <div className="flex-1 overflow-y-auto p-6 space-y-6" aria-live="polite" aria-relevant="additions text">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <p className="text-xl font-medium mb-2">Internal RAG Assistant</p>
            <p className="text-sm">Hold the button below to ask a question.</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <ChatMessage key={idx} msg={msg} onOpenCitation={onOpenCitation} />
          ))
        )}
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-900/80 backdrop-blur pb-8">
        <PushToTalk onAudioComplete={handleAudioComplete} isProcessing={isProcessing} />
      </div>
    </div>
  );
}
