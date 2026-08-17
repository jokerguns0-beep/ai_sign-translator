"use client";

import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Volume2, Send, Trash2 } from "lucide-react";
import { useSpeech } from "@/hooks/useSpeech";
import { REPLY_CATEGORIES } from "@/lib/replyPhrases";

interface SentItem {
  id: string;
  text: string;
  timestamp: number;
}

export default function ReplyPage() {
  const [displayText, setDisplayText] = useState("");
  const [customText, setCustomText] = useState("");
  const [activeCategory, setActiveCategory] = useState(REPLY_CATEGORIES[0].id);
  const [history, setHistory] = useState<SentItem[]>([]);

  const speech = useSpeech();

  const send = useCallback(
    (text: string) => {
      if (!text.trim()) return;
      setDisplayText(text);
      speech.speak(text);
      setHistory((prev) => [{ id: crypto.randomUUID(), text, timestamp: Date.now() }, ...prev].slice(0, 30));
    },
    [speech]
  );

  const sendCustom = () => {
    send(customText);
    setCustomText("");
  };

  const category = REPLY_CATEGORIES.find((c) => c.id === activeCategory) ?? REPLY_CATEGORIES[0];

  return (
    <main className="min-h-screen px-4 py-6 md:px-8 md:py-10 max-w-7xl mx-auto">
      <header className="mb-8">
        <p className="font-mono text-[11px] text-signal-amber uppercase tracking-[0.2em] mb-2">
          Продолжение разговора
        </p>
        <h1 className="font-display text-2xl md:text-3xl font-medium text-white">
          Выберите ответ — покажите экран собеседнику
        </h1>
      </header>

      {/* Large display - this is the screen shown to the deaf/hard-of-hearing person */}
      <div className="mb-6 rounded-3xl border border-graphite-700 bg-graphite-900 p-6 md:p-10 min-h-[160px] flex items-center justify-center text-center relative overflow-hidden">
        <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full bg-signal-amber/[0.06] blur-3xl pointer-events-none" />
        <AnimatePresence mode="wait">
          {displayText ? (
            <motion.p
              key={displayText}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="font-display text-3xl md:text-5xl font-medium text-white leading-snug relative"
            >
              {displayText}
            </motion.p>
          ) : (
            <p className="font-body text-graphite-600 text-lg relative">
              Выберите фразу ниже или напишите свою — она появится здесь крупным текстом и озвучится
            </p>
          )}
        </AnimatePresence>
      </div>

      {/* Custom text input */}
      <div className="mb-6 flex gap-3">
        <input
          type="text"
          value={customText}
          onChange={(e) => setCustomText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendCustom()}
          placeholder="Напишите свой ответ…"
          className="flex-1 rounded-2xl bg-graphite-900 border border-graphite-700 px-4 py-3 font-body text-white placeholder:text-graphite-700 focus:outline-none focus:border-signal-teal/50"
        />
        <button
          onClick={sendCustom}
          disabled={!customText.trim()}
          className="shrink-0 flex items-center gap-2 px-5 py-3 rounded-2xl bg-signal-teal text-graphite-950 font-display font-medium disabled:opacity-30 disabled:cursor-not-allowed hover:bg-signal-teal/90 transition-colors"
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline">Показать</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-6">
        {/* Quick replies */}
        <div className="rounded-2xl border border-graphite-700 bg-graphite-900 p-5">
          <div className="flex flex-wrap gap-2 mb-5">
            {REPLY_CATEGORIES.map((c) => (
              <button
                key={c.id}
                onClick={() => setActiveCategory(c.id)}
                className={`px-3.5 py-1.5 rounded-full text-xs md:text-sm font-body transition-colors ${
                  c.id === activeCategory
                    ? "bg-signal-teal/15 text-signal-teal border border-signal-teal/40"
                    : "text-graphite-600 border border-graphite-700 hover:text-white"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {category.phrases.map((phrase) => (
              <button
                key={phrase}
                onClick={() => send(phrase)}
                className="group text-left px-4 py-3.5 rounded-xl bg-graphite-800/60 border border-graphite-700 hover:border-signal-teal/50 hover:bg-graphite-800 transition-colors flex items-center justify-between gap-3"
              >
                <span className="font-body text-sm text-white">{phrase}</span>
                <Volume2 className="w-4 h-4 text-graphite-700 group-hover:text-signal-teal shrink-0 transition-colors" />
              </button>
            ))}
          </div>
        </div>

        {/* Sent history */}
        <div className="rounded-2xl border border-graphite-700 bg-graphite-900 p-5 flex flex-col gap-3 min-h-[300px]">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-sm text-graphite-600 uppercase tracking-wide">История ответов</h2>
            {history.length > 0 && (
              <button
                onClick={() => setHistory([])}
                className="text-graphite-700 hover:text-signal-coral transition-colors"
                aria-label="Очистить историю"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto flex flex-col gap-2">
            <AnimatePresence initial={false}>
              {history.map((item) => (
                <motion.button
                  key={item.id}
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  onClick={() => send(item.text)}
                  className="text-left rounded-lg bg-graphite-800/50 px-3 py-2 hover:bg-graphite-800 transition-colors"
                >
                  <p className="font-body text-sm text-graphite-600">{item.text}</p>
                  <p className="font-mono text-[10px] text-graphite-700 mt-0.5">
                    {new Date(item.timestamp).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </motion.button>
              ))}
            </AnimatePresence>
            {history.length === 0 && <p className="font-body text-sm text-graphite-700">Пока пусто</p>}
          </div>
        </div>
      </div>
    </main>
  );
}
