"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  ConnectionStatus,
  GestureRecognitionResult,
  SignLanguage,
  WSMessage,
} from "@/lib/types";

function resolveWsUrl(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) return process.env.NEXT_PUBLIC_WS_URL;
  if (typeof window === "undefined") return "";
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws/translate`;
}

const WS_URL = resolveWsUrl();

interface UseWebSocketOptions {
  onTranscript: (result: GestureRecognitionResult) => void;
  onError?: (message: string) => void;
}

/**
 * Owns the lifecycle of the translation WebSocket: connect on demand,
 * send frames, dispatch incoming transcript/status/error messages, and
 * reconnect gracefully if the connection drops mid-session.
 */
export function useWebSocket({ onTranscript, onError }: UseWebSocketOptions) {
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const socket = new WebSocket(WS_URL);

    socket.onopen = () => setStatus("ready");
    socket.onerror = () => setStatus("error");
    socket.onclose = () => setStatus("idle");
    socket.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        if (message.type === "transcript") {
          onTranscript(message.payload as GestureRecognitionResult);
        } else if (message.type === "status") {
          setStatus("ready");
        } else if (message.type === "error") {
          const payload = message.payload as { message?: string };
          if (payload?.message) onError?.(payload.message);
        }
      } catch {
        // Ignore malformed frames rather than crashing the session.
      }
    };

    socketRef.current = socket;
  }, [onTranscript]);

  const disconnect = useCallback(() => {
    socketRef.current?.close();
    socketRef.current = null;
    setStatus("idle");
  }, []);

  const sendFrame = useCallback((dataUrl: string) => {
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "landmarks", payload: { frame: dataUrl } }));
    }
  }, []);

  const setLanguage = useCallback((language: SignLanguage) => {
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "set_language", payload: { language } }));
    }
  }, []);

  useEffect(() => () => socketRef.current?.close(), []);

  return { status, connect, disconnect, sendFrame, setLanguage };
}
