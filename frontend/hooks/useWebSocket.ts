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
const RECONNECT_DELAY_MS = 800;

interface UseWebSocketOptions {
  onTranscript: (result: GestureRecognitionResult) => void;
  onError?: (message: string) => void;
  onEvent?: (event: string) => void;
}

/**
 * Owns the lifecycle of the translation WebSocket: connect on demand,
 * send frames, dispatch incoming transcript/status/error messages, and
 * reconnect automatically if the connection drops mid-session (Render's
 * free tier proxy closes idle-looking WS connections after ~50s).
 */
export function useWebSocket({ onTranscript, onError, onEvent }: UseWebSocketOptions) {
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const socketRef = useRef<WebSocket | null>(null);
  const wantConnectedRef = useRef(false);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearReconnectTimer = () => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  };

  const openSocket = useCallback(() => {
    setStatus("connecting");
    onEvent?.(`подключаюсь к ${WS_URL}`);
    const socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      setStatus("ready");
      onEvent?.("сокет открыт");
    };
    socket.onerror = () => {
      onEvent?.("ошибка сокета (см. code в onclose)");
    };
    socket.onclose = (event) => {
      onEvent?.(`сокет закрыт: code=${event.code} reason="${event.reason || "—"}" clean=${event.wasClean}`);
      socketRef.current = null;

      if (wantConnectedRef.current) {
        // Unintended drop (Render free-tier proxy timeout etc.) — reconnect quietly.
        setStatus("connecting");
        clearReconnectTimer();
        reconnectTimerRef.current = setTimeout(() => {
          if (wantConnectedRef.current) openSocket();
        }, RECONNECT_DELAY_MS);
      } else {
        setStatus("idle");
      }
    };
    socket.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        onEvent?.(`получено: type=${message.type}`);
        if (message.type === "transcript") {
          onTranscript(message.payload as GestureRecognitionResult);
        } else if (message.type === "status") {
          setStatus("ready");
        } else if (message.type === "error") {
          const payload = message.payload as { message?: string };
          if (payload?.message) onError?.(payload.message);
        }
      } catch (err) {
        onEvent?.(`не смог разобрать сообщение: ${err}`);
      }
    };

    socketRef.current = socket;
  }, [onTranscript, onError, onEvent]);

  const connect = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) return;
    wantConnectedRef.current = true;
    clearReconnectTimer();
    openSocket();
  }, [openSocket]);

  const disconnect = useCallback(() => {
    wantConnectedRef.current = false;
    clearReconnectTimer();
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

  useEffect(
    () => () => {
      wantConnectedRef.current = false;
      clearReconnectTimer();
      socketRef.current?.close();
    },
    []
  );

  return { status, connect, disconnect, sendFrame, setLanguage };
}