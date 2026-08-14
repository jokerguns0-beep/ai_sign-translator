"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { TranscriptItem } from "@/lib/types";

interface TranscriptPanelProps {
  currentText: string;
  currentConfidence: number;
  history: TranscriptItem[];
  onClear: () => void;
  onCopy: () => void;
}

export default function TranscriptPanel({
  currentText,
  currentConfidence,
  history,
  onClear,
  onCopy,
}: TranscriptPanelProps) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-graphite-700 bg-graphite-900 p-5 flex-1 min-h-0">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-sm text-graphite-600 uppercase tracking-wide">Распознанный текст</h2>
        <div className="flex gap-2">
          <button
            onClick={onCopy}
            className="text-xs font-mono px-2 py-1 rounded-md bg-graphite-800 text-graphite-600 hover:text-signal-teal"
          >
            Копировать
          </button>
          <button
            onClick={onClear}
            className="text-xs font-mono px-2 py-1 rounded-md bg-graphite-800 text-graphite-600 hover:text-signal-coral"
          >
            Очистить
          </button>
        </div>
      </div>

      <div className="min-h-[88px] rounded-xl bg-graphite-950 border border-graphite-700 p-4 flex flex-col justify-center">
        {currentText ? (
          <>
            <p className="font-display text-2xl text-white leading-snug">{currentText}</p>
            <p className="font-mono text-xs text-signal-teal mt-2">
              уверенность: {(currentConfidence * 100).toFixed(0)}%
            </p>
          </>
        ) : (
          <p className="font-body text-graphite-600">Покажите жест перед камерой…</p>
        )}
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-2">
        <h3 className="font-mono text-[11px] text-graphite-600 uppercase tracking-wide sticky top-0 bg-graphite-900 pb-1">
          Журнал
        </h3>
        <AnimatePresence initial={false}>
          {history.map((item) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center justify-between gap-3 rounded-lg bg-graphite-800/60 px-3 py-2"
            >
              <span className="font-body text-sm text-graphite-600">{item.text}</span>
              <span className="font-mono text-[10px] text-graphite-600">
                {new Date(item.timestamp).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
        {history.length === 0 && <p className="font-body text-sm text-graphite-700">Пока пусто</p>}
      </div>
    </div>
  );
}
