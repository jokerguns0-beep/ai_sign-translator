export type SignLanguage = "rsl" | "asl" | "bsl";

export interface GestureAlternative {
  text: string;
  confidence: number;
}

export interface GestureRecognitionResult {
  recognized_gesture: string;
  confidence: number;
  predicted_word: string | null;
  predicted_phrase: string | null;
  alternatives: GestureAlternative[];
  language: SignLanguage;
  confirmed: boolean;
}

export type WSMessageType = "landmarks" | "transcript" | "status" | "error" | "set_language";

export interface WSMessage<T = unknown> {
  type: WSMessageType;
  payload: T;
}

export interface TranscriptItem {
  id: string;
  text: string;
  confidence: number;
  timestamp: number;
}

export type ConnectionStatus = "idle" | "connecting" | "ready" | "error";
