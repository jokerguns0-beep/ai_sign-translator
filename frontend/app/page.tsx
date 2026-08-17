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
  const [isConfirmed, setIsConfirmed] = useState(true);
  const [debugLog, setDebugLog] = useState<string[]>([]);
  const [showDebug, setShowDebug] = useState(false);

  const speech = useSpeech();

  const logEvent = useCallback((event: string) => {
    const time = new Date().toLocaleTimeString("ru-RU", { hour12: false });
    setDebugLog((prev) => [`${time} — ${event}`, ...prev].slice(0, 40));
  }, []);

  const handleTranscript = useCallback(
    (result: GestureRecognitionResult) => {
      const text = result.predicted_phrase || result.predicted_word || result.recognized_gesture;
      if (!text) return;
      setBackendError(null);
      setCurrentText(text);
      setCurrentConfidence(result.confidence);
      setIsConfirmed(result.confirmed);
      if (result.confirmed) {
        setHistory((prev) => [{ id: crypto.randomUUID(), text, confidence: result.confidence, timestamp: Date.now() }, ...prev].slice(0, 50));
        speech.speak(text);
      }
    },
    [speech]
  );

  const { status, connect, disconnect, sendFrame, setLanguage: sendLanguage } = useWebSocket({
    onTranscript: handleTranscript,
    onError: setBackendError,
    onEvent: logEvent,
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
      <header className="mb-8 flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-[11px] text-signal-teal uppercase tracking-[0.2em] mb-2">
            Русский жестовый язык · распознавание в реальном времени
          </p>
          <h1 className="font-display text-2xl md:text-3xl font-medium text-white">
            Покажите жест — я переведу его в текст и озвучу
          </h1>
        </div>
        <button
          onClick={() => setShowDebug((v) => !v)}
          className="shrink-0 text-xs font-mono px-3 py-2 rounded-lg bg-graphite-900 border border-graphite-700 text-graphite-600 hover:text-signal-teal hover:border-signal-teal/40 transition-colors"
        >
          {showDebug ? "Скрыть журнал" : "Журнал соединения"}
        </button>
      </header>

      {showDebug && (
        <div className="mb-6 rounded-2xl border border-graphite-700 bg-graphite-950 p-4 max-h-64 overflow-y-auto">
          <p className="font-mono text-[11px] text-graphite-600 uppercase tracking-wide mb-2 sticky top-0">
            Журнал WebSocket-соединения (для диагностики)
          </p>
          {debugLog.length === 0 ? (
            <p className="font-mono text-xs text-graphite-700">Пока пусто — запусти камеру</p>
          ) : (
            <ul className="flex flex-col gap-1">
              {debugLog.map((line, i) => (
                <li key={i} className="font-mono text-[11px] text-graphite-600 break-all">
                  {line}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {backendError && (
        <div className="mb-6 rounded-2xl border border-signal-coral/40 bg-signal-coral/10 px-4 py-3 text-sm text-signal-coral font-body">
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
            isConfirmed={isConfirmed}
            history={history}
            onClear={clearTranscript}
            onCopy={copyTranscript}
          />
        </div>
      </div>
    </main>
  );
}
