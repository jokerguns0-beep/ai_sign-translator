"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Wraps the browser's Web Speech API (SpeechSynthesis) for automatic
 * read-aloud of recognized text, with adjustable rate/volume/voice.
 * This is the "web version" TTS path - the Python pyttsx3 engine in the
 * backend is only used by the local/desktop entry point.
 */
export function useSpeech() {
  const [enabled, setEnabled] = useState(true);
  const [rate, setRate] = useState(1);
  const [volume, setVolume] = useState(1);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voiceURI, setVoiceURI] = useState<string | undefined>(undefined);
  const supported = useRef(typeof window !== "undefined" && "speechSynthesis" in window);

  useEffect(() => {
    if (!supported.current) return;
    const loadVoices = () => setVoices(window.speechSynthesis.getVoices());
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!supported.current || !enabled || !text.trim()) return;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = rate;
      utterance.volume = volume;
      const voice = voices.find((v) => v.voiceURI === voiceURI);
      if (voice) utterance.voice = voice;
      window.speechSynthesis.speak(utterance);
    },
    [enabled, rate, volume, voices, voiceURI]
  );

  return { speak, enabled, setEnabled, rate, setRate, volume, setVolume, voices, voiceURI, setVoiceURI };
}
