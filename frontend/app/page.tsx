"use client";

import { useCallback, useState } from "react";
import CameraView from "@/components/CameraView";
import ControlPanel from "@/components/ControlPanel";
import TranscriptPanel from "@/components/TranscriptPanel";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useSpeech } from "@/hooks/useSpeech";
import type { GestureRecognitionResult, SignLanguage, TranscriptItem } from "@/lib/types";

export default function Home() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [language, setLanguage] = useState<SignLanguage>("rsl");
  const [currentText, setCurrentText] = useState("");
  const [currentConfidence, setCurrentConfidence] = useState(0);
  const [history, setHistory] = useState<TranscriptItem[]>([]);
  const [backendError, setBackendError] = useState<string | null>(null);

  const speech = useSpeech();

  const handleTranscript = useCallback(
    (result: GestureRecognitionResult) => {
      const text = result.predicted_phrase || result.predicted_word || result.recognized_gesture;
      if (!text) return;
      setBackendError(null);
      setCurrentText(text);
      setCurrentConfidence(result.confidence);
      setHistory((prev) => [{ id: crypto.randomUUID(), text, confidence: result.confidence, timestamp: Date.now() }, ...prev].slice(0, 50));
      speech.speak(text);
    },
    [speech]
  );

  const { status, connect, disconnect, sendFrame, setLanguage: sendLanguage } = useWebSocket({
    onTranscript: handleTranscript,
    onError: setBackendError,
  });

  const toggleStreaming = () => {
    if (isStreaming) {
      disconnect();
      setIsStreaming(false);
    } else {
      connect();
      setIsStreaming(true);
    }
  };

  const changeLanguage = (lang: SignLanguage) => {
    setLanguage(lang);
    sendLanguage(lang);
  };

  const clearTranscript = () => {
    setCurrentText("");
    setCurrentConfidence(0);
    setHistory([]);
  };

  const copyTranscript = async () => {
    if (currentText) await navigator.clipboard.writeText(currentText);
  };

  return (
    <main className="min-h-screen px-4 py-6 md:px-8 md:py-10 max-w-7xl mx-auto">
      <header className="mb-8">
        <p className="font-mono text-xs text-signal-teal uppercase tracking-widest mb-2">
          Перевод жестового языка · в реальном времени
        </p>
        <h1 className="font-display text-3xl md:text-4xl font-medium">AI Sign Language Translator</h1>
      </header>

      {backendError && (
        <div className="mb-6 rounded-xl border border-signal-coral/40 bg-signal-coral/10 px-4 py-3 text-sm text-signal-coral font-body">
          Ошибка сервера: {backendError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-6">
        <div className="flex flex-col gap-6">
          <CameraView active={isStreaming} onFrame={sendFrame} />
        </div>

        <div className="flex flex-col gap-6 min-h-[520px]">
          <ControlPanel
            isStreaming={isStreaming}
            onToggleStreaming={toggleStreaming}
            status={status}
            language={language}
            onLanguageChange={changeLanguage}
            speechEnabled={speech.enabled}
            onToggleSpeech={() => speech.setEnabled((v) => !v)}
            speechRate={speech.rate}
            onSpeechRateChange={speech.setRate}
          />
          <TranscriptPanel
            currentText={currentText}
            currentConfidence={currentConfidence}
            history={history}
            onClear={clearTranscript}
            onCopy={copyTranscript}
          />
        </div>
      </div>
    </main>
  );
}
