"use client";

import type { ConnectionStatus, SignLanguage } from "@/lib/types";

interface ControlPanelProps {
  isStreaming: boolean;
  onToggleStreaming: () => void;
  status: ConnectionStatus;
  language: SignLanguage;
  onLanguageChange: (lang: SignLanguage) => void;
  speechEnabled: boolean;
  onToggleSpeech: () => void;
  speechRate: number;
  onSpeechRateChange: (rate: number) => void;
}

const LANGUAGES: { value: SignLanguage; label: string; available: boolean }[] = [
  { value: "rsl", label: "РЖЯ (русский)", available: true },
  { value: "asl", label: "ASL (скоро)", available: false },
  { value: "bsl", label: "BSL (скоро)", available: false },
];

const STATUS_LABEL: Record<ConnectionStatus, string> = {
  idle: "Остановлено",
  connecting: "Подключение…",
  ready: "Модель активна",
  error: "Ошибка соединения",
};

const STATUS_COLOR: Record<ConnectionStatus, string> = {
  idle: "text-graphite-600",
  connecting: "text-signal-amber",
  ready: "text-signal-teal",
  error: "text-signal-coral",
};

export default function ControlPanel({
  isStreaming,
  onToggleStreaming,
  status,
  language,
  onLanguageChange,
  speechEnabled,
  onToggleSpeech,
  speechRate,
  onSpeechRateChange,
}: ControlPanelProps) {
  return (
    <div className="flex flex-col gap-5 rounded-2xl border border-graphite-700 bg-graphite-900 p-5">
      <div className="flex items-center justify-between">
        <span className={`font-mono text-xs ${STATUS_COLOR[status]}`}>
          {isStreaming && <span className="inline-block w-2 h-2 rounded-full bg-signal-amber mr-2 animate-pulse-rec" />}
          {STATUS_LABEL[status]}
        </span>
      </div>

      <button
        onClick={onToggleStreaming}
        className={`w-full py-3 rounded-xl font-display font-medium transition-colors ${
          isStreaming
            ? "bg-signal-coral/20 text-signal-coral border border-signal-coral/40 hover:bg-signal-coral/30"
            : "bg-signal-teal text-graphite-950 hover:bg-signal-teal/90"
        }`}
      >
        {isStreaming ? "Остановить камеру" : "Запустить камеру"}
      </button>

      <div>
        <label className="text-xs font-mono text-graphite-600 mb-2 block">Язык жестов</label>
        <div className="grid grid-cols-1 gap-2">
          {LANGUAGES.map((l) => (
            <button
              key={l.value}
              disabled={!l.available}
              onClick={() => onLanguageChange(l.value)}
              className={`text-left px-3 py-2 rounded-lg text-sm font-body transition-colors ${
                language === l.value
                  ? "bg-signal-teal/15 text-signal-teal border border-signal-teal/40"
                  : "text-graphite-600 border border-transparent hover:bg-graphite-800"
              } ${!l.available ? "opacity-40 cursor-not-allowed" : ""}`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs font-mono text-graphite-600">Озвучивание</label>
          <button
            onClick={onToggleSpeech}
            className={`text-xs px-2 py-1 rounded-md font-mono ${
              speechEnabled ? "bg-signal-teal/15 text-signal-teal" : "bg-graphite-800 text-graphite-600"
            }`}
          >
            {speechEnabled ? "Вкл" : "Выкл"}
          </button>
        </div>
        <input
          type="range"
          min={0.5}
          max={2}
          step={0.1}
          value={speechRate}
          onChange={(e) => onSpeechRateChange(parseFloat(e.target.value))}
          className="w-full accent-signal-teal"
          disabled={!speechEnabled}
        />
        <div className="text-[10px] font-mono text-graphite-600 mt-1">Скорость речи: {speechRate.toFixed(1)}x</div>
      </div>
    </div>
  );
}
