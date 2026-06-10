import React, { useState, useEffect, useRef } from 'react';
import PushToTalk from './PushToTalk';
import { useAuth } from '../context/AuthContext';

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const { token } = useAuth();
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const currentTextRef = useRef('');

  useEffect(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = import.meta.env.VITE_WS_URL
      || `${wsProtocol}//${window.location.host}/voice/ws`;
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => console.log("WebSocket connected");
    
    wsRef.current.onmessage = async (event) => {
      const msg = JSON.parse(event.data);
      
      if (msg.type === 'status') {
        if (msg.data === 'Done') {
          setIsProcessing(false);
          currentTextRef.current = '';
        }
      } else if (msg.type === 'transcription') {
        setMessages(prev => [...prev, { role: 'user', content: msg.data }]);
        setMessages(prev => [...prev, { role: 'assistant', content: '', citations: [] }]);
      } else if (msg.type === 'text') {
        currentTextRef.current += msg.data + ' ';
        setMessages(prev => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1].content = currentTextRef.current;
          return newMsgs;
        });
      } else if (msg.type === 'citations') {
        setMessages(prev => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1].citations = msg.data;
          return newMsgs;
        });
      } else if (msg.type === 'audio') {
        // Play audio chunk
        playAudio(msg.data);
      } else if (msg.type === 'error') {
        console.error("WS Error:", msg.data);
        setIsProcessing(false);
      }
    };

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const playAudio = async (base64Data) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    const binaryStr = window.atob(base64Data);
    const len = binaryStr.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryStr.charCodeAt(i);
    }
    const audioData = await audioContextRef.current.decodeAudioData(bytes.buffer);
    const source = audioContextRef.current.createBufferSource();
    source.buffer = audioData;
    source.connect(audioContextRef.current.destination);
    source.start(0);
  };

  const handleAudioComplete = (audioBlob) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setIsProcessing(true);
      wsRef.current.send(audioBlob);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-900 relative">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <p className="text-xl font-medium mb-2">Internal RAG Assistant</p>
            <p className="text-sm">Hold the button below to ask a question.</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-2xl rounded-2xl px-6 py-4 ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'glass-panel text-slate-100'}`}>
                <p className="leading-relaxed">{msg.content}</p>
                
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-700/50 flex flex-wrap gap-2">
                    {msg.citations.map(cit => (
                      <div key={cit.id} className="text-xs bg-slate-800/80 px-2 py-1 rounded text-blue-300 border border-slate-700">
                        {cit.title || cit.id}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-900/80 backdrop-blur pb-8">
        <PushToTalk onAudioComplete={handleAudioComplete} isProcessing={isProcessing} />
      </div>
    </div>
  );
}
