import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { Mic, Square, Loader } from 'lucide-react';

function PushToTalk({ onAudioComplete, isProcessing }) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const recordingRef = useRef(false);

  const releaseStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function warmMic() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (!cancelled) {
          streamRef.current = stream;
        } else {
          stream.getTracks().forEach((track) => track.stop());
        }
      } catch {
        // Permission denied or no device — handled on first press.
      }
    }

    warmMic();
    return () => {
      cancelled = true;
      releaseStream();
    };
  }, [releaseStream]);

  const startRecording = useCallback(async () => {
    if (isProcessing || recordingRef.current) {
      return;
    }

    recordingRef.current = true;
    setIsRecording(true);

    try {
      if (!streamRef.current || !streamRef.current.active) {
        streamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      const mediaRecorder = new MediaRecorder(streamRef.current, { mimeType: 'audio/webm' });
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
      };

      mediaRecorder.start();
    } catch (err) {
      console.error('Error accessing microphone:', err);
      recordingRef.current = false;
      setIsRecording(false);
      alert('Microphone access is required.');
    }
  }, [isProcessing, onAudioComplete]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingRef.current) {
      mediaRecorderRef.current.stop();
      recordingRef.current = false;
      setIsRecording(false);
    }
  }, []);

  const handlePointerDown = (event) => {
    event.preventDefault();
    startRecording();
  };

  const handlePointerUp = (event) => {
    event.preventDefault();
    stopRecording();
  };

  return (
    <div className="flex flex-col items-center justify-center p-6">
      <button
        type="button"
        aria-label={isProcessing ? 'Processing your question' : isRecording ? 'Release to send' : 'Hold to speak'}
        aria-pressed={isRecording}
        aria-busy={isProcessing}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerLeave={isRecording ? handlePointerUp : undefined}
        onPointerCancel={handlePointerUp}
        disabled={isProcessing}
        className={`mic-control-btn relative flex h-24 w-24 touch-none select-none items-center justify-center rounded-full text-white shadow-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-300 ${
          isRecording ? 'mic-recording-active scale-[0.97] bg-red-500' :
          isProcessing ? 'cursor-not-allowed bg-slate-600' : 'bg-blue-600 hover:bg-blue-500'
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

      <p className="mt-6 text-sm font-medium text-slate-400">
        {isProcessing ? 'Processing request...' :
         isRecording ? 'Release to send' : 'Hold to speak'}
      </p>
    </div>
  );
}

export default memo(PushToTalk);
