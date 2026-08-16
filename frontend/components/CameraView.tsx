"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { HandLandmarker } from "@mediapipe/tasks-vision";

interface CameraViewProps {
  active: boolean;
  onFrame: (dataUrl: string) => void;
  captureIntervalMs?: number;
}

const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16],
  [13, 17], [17, 18], [18, 19], [19, 20],
  [0, 17],
];

/**
 * Renders the live camera feed, draws a hand-landmark overlay client-side
 * (purely for visual feedback / quality indication) via MediaPipe Tasks
 * Vision, tracks FPS, and periodically emits captured frames as base64
 * JPEG data URLs for the backend recognition pipeline.
 */
export default function CameraView({ active, onFrame, captureIntervalMs = 120 }: CameraViewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const landmarkerRef = useRef<HandLandmarker | null>(null);
  const rafRef = useRef<number>();
  const lastCaptureRef = useRef<number>(0);
  const fpsCounterRef = useRef<{ count: number; last: number }>({ count: 0, last: performance.now() });

  const [fps, setFps] = useState(0);
  const [handsDetected, setHandsDetected] = useState(0);
  const [cameraError, setCameraError] = useState<string | null>(null);

  useEffect(() => {
    let stream: MediaStream | null = null;

    async function setup() {
      try {
        const { HandLandmarker, FilesetResolver } = await import("@mediapipe/tasks-vision");
        const vision = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
        );
        landmarkerRef.current = await HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath:
              "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
            delegate: "GPU",
          },
          runningMode: "VIDEO",
          numHands: 2,
        });
      } catch (err) {
        console.error("Failed to load hand landmarker", err);
      }

      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: { ideal: 640 } },
          audio: false,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch (err) {
        setCameraError("Не удалось получить доступ к камере. Проверьте разрешения браузера.");
      }
    }

    if (active) setup();

    return () => {
      stream?.getTracks().forEach((t) => t.stop());
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [active]);

  const drawOverlay = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const landmarker = landmarkerRef.current;
    if (!video || !canvas || !landmarker || video.readyState < 2) {
      rafRef.current = requestAnimationFrame(drawOverlay);
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const result = landmarker.detectForVideo(video, performance.now());
    setHandsDetected(result.landmarks?.length ?? 0);

    ctx.strokeStyle = "#3FD6C2";
    ctx.fillStyle = "#F2A93B";
    ctx.lineWidth = 2;

    for (const hand of result.landmarks ?? []) {
      for (const [a, b] of HAND_CONNECTIONS) {
        const p1 = hand[a];
        const p2 = hand[b];
        ctx.beginPath();
        ctx.moveTo(p1.x * canvas.width, p1.y * canvas.height);
        ctx.lineTo(p2.x * canvas.width, p2.y * canvas.height);
        ctx.stroke();
      }
      for (const point of hand) {
        ctx.beginPath();
        ctx.arc(point.x * canvas.width, point.y * canvas.height, 3, 0, 2 * Math.PI);
        ctx.fill();
      }
    }

    // FPS tracking
    const counter = fpsCounterRef.current;
    counter.count += 1;
    const now = performance.now();
    if (now - counter.last >= 1000) {
      setFps(counter.count);
      counter.count = 0;
      counter.last = now;
    }

    // Throttled frame capture -> backend, only while a hand is actually
    // visible. The backend's CPU is the bottleneck (esp. on constrained
    // free-tier hosting), so skipping empty frames here - rather than
    // making the backend decode+run MediaPipe on them just to discard
    // them - is the single biggest lever for faster, cheaper recognition.
    const handVisible = (result.landmarks?.length ?? 0) > 0;
    if (handVisible && now - lastCaptureRef.current >= captureIntervalMs) {
      lastCaptureRef.current = now;
      const captureCanvas = document.createElement("canvas");
      captureCanvas.width = video.videoWidth;
      captureCanvas.height = video.videoHeight;
      const captureCtx = captureCanvas.getContext("2d");
      if (captureCtx) {
        captureCtx.drawImage(video, 0, 0);
        onFrame(captureCanvas.toDataURL("image/jpeg", 0.7));
      }
    }

    rafRef.current = requestAnimationFrame(drawOverlay);
  }, [captureIntervalMs, onFrame]);

  useEffect(() => {
    if (active) {
      rafRef.current = requestAnimationFrame(drawOverlay);
    }
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [active, drawOverlay]);

  return (
    <div className="relative w-full aspect-video overflow-hidden rounded-2xl bg-graphite-900 border border-graphite-700">
      <video ref={videoRef} muted playsInline className="w-full h-full object-cover -scale-x-100" />
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full -scale-x-100" />

      {!active && (
        <div className="absolute inset-0 flex items-center justify-center text-graphite-600 font-body">
          Камера выключена
        </div>
      )}

      {cameraError && (
        <div className="absolute inset-0 flex items-center justify-center bg-graphite-950/90 text-signal-coral text-center px-6 font-body">
          {cameraError}
        </div>
      )}

      <div className="absolute top-3 left-3 flex gap-2 font-mono text-xs">
        <span className="bg-graphite-950/70 text-signal-teal px-2 py-1 rounded-md">{fps} FPS</span>
        <span className="bg-graphite-950/70 text-graphite-600 px-2 py-1 rounded-md">
          рук в кадре: {handsDetected}
        </span>
      </div>
    </div>
  );
}
