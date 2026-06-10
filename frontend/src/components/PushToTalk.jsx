import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Loader } from 'lucide-react';

export default function PushToTalk({ onAudioComplete, isProcessing }) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    if (isProcessing) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        onAudioComplete(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access is required.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-6">
      <div className="relative">
        {isRecording && (
          <div className="absolute inset-0 bg-blue-500 rounded-full animate-ping opacity-75"></div>
        )}
        
        <button
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onMouseLeave={stopRecording}
          onTouchStart={startRecording}
          onTouchEnd={stopRecording}
          disabled={isProcessing}
          className={`relative z-10 w-24 h-24 rounded-full flex items-center justify-center text-white shadow-xl transition-all duration-200 ${
            isRecording ? 'bg-red-500 scale-95' : 
            isProcessing ? 'bg-slate-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 hover:scale-105'
          }`}
        >
          {isProcessing ? (
            <Loader size={36} className="animate-spin" />
          ) : isRecording ? (
            <Square size={36} />
          ) : (
            <Mic size={48} />
          )}
        </button>
      </div>
      
      <p className="mt-6 text-slate-400 text-sm font-medium">
        {isProcessing ? 'Processing request...' : 
         isRecording ? 'Release to send' : 'Hold to speak'}
      </p>
    </div>
  );
}
