# Архитектура AI Sign Language Translator

## 1. Структура проекта

```
ai-sign-translator/
├── backend/
│   ├── main.py                  # точка входа FastAPI
│   ├── config/settings.py       # Config (Pydantic Settings)
│   ├── models/schemas.py        # все Pydantic-схемы (Landmark, WSMessage, History...)
│   ├── services/
│   │   ├── camera_manager.py    # CameraManager (только для локального режима)
│   │   ├── frame_processor.py   # FrameProcessor
│   │   ├── landmark_detector.py # LandmarkDetector (MediaPipe Hands+Pose)
│   │   ├── gesture_buffer.py    # GestureSequenceBuffer (ring buffer)
│   │   ├── gesture_recognizer.py# GestureRecognizer (когда стрелять в Gemini)
│   │   ├── gemini_client.py     # GeminiClient
│   │   ├── translator.py        # Translator (facade сессии)
│   │   ├── speech_engine.py     # SpeechEngine (pyttsx3, локальный режим)
│   │   ├── history_manager.py   # HistoryManager (SQLite, TXT/PDF export)
│   │   ├── api_service.py       # APIService (общий HTTP-клиент с retry)
│   │   └── app_controller.py    # AppController (локальный запуск без веба)
│   ├── routers/
│   │   ├── websocket_router.py  # /ws/translate
│   │   └── history_router.py    # /api/history
│   ├── utils/logger.py          # Logger (loguru)
│   └── tests/test_api.py
├── frontend/
│   ├── app/                     # Next.js App Router (page.tsx, layout.tsx)
│   ├── components/              # CameraView, ControlPanel, TranscriptPanel
│   ├── hooks/                   # useWebSocket, useSpeech
│   └── lib/types.ts             # TS-типы, зеркалящие backend/models/schemas.py
└── docs/
```

## 2. Назначение ключевых файлов

- **`config/settings.py`** — единственная точка чтения `.env`. Больше нигде в коде `os.environ` не используется напрямую — это упрощает тестирование и защищает от утечки ключей.
- **`models/schemas.py`** — контракт данных между всеми слоями (CV → буфер → Gemini → WebSocket → фронтенд). TypeScript-типы во фронтенде — его зеркало.
- **`services/*`** — каждый класс делает ровно одну вещь (SRP из SOLID): `FrameProcessor` только декодирует кадры, `LandmarkDetector` только считает landmarks, `GestureSequenceBuffer` только хранит окно кадров и т.д. Это позволяет менять, например, движок TTS или буферизацию, не трогая остальной код.
- **`routers/websocket_router.py`** — единственная точка входа для реального времени. Именно здесь `Translator` создаётся заново на каждое соединение, поэтому сессии разных пользователей никогда не пересекаются.

## 3. Поток данных (data flow)

```
Браузер (getUserMedia)
   │  JPEG-кадр раз в ~120мс, base64 data URL
   ▼
WebSocket /ws/translate
   │
   ▼
Translator.process_frame()
   ├─ FrameProcessor.decode → cv2 image (BGR)
   ├─ FrameProcessor.preprocess → resize + BGR→RGB
   ├─ LandmarkDetector.detect → FrameLandmarks (руки + верхняя часть тела)
   ├─ GestureSequenceBuffer.add → ring buffer (30–120 кадров)
   └─ GestureRecognizer.maybe_recognize
        │  (срабатывает только когда буфер заполнен И прошёл cooldown)
        ▼
      GeminiClient.recognize → структурированный JSON (жест/слово/фраза/альтернативы)
        │
        ▼
      HistoryManager.add (SQLite)
        │
        ▼
WebSocket → фронтенд { type: "transcript", payload: {...} }
   │
   ▼
useWebSocket.onTranscript → TranscriptPanel (текст) + useSpeech.speak (Web Speech API)
```

Важно: видео **никогда не блокируется** ожиданием Gemini — кадры продолжают декодироваться и складываться в буфер, пока предыдущий запрос к Gemini ещё выполняется (это гарантирует `asyncio.Lock` в `GestureRecognizer`).

## 4. Почему такая архитектура

- **Landmarks вместо сырых кадров в Gemini.** Отправка 30–120 полных изображений на каждое распознавание была бы дорого и медленно. Вместо этого в Gemini уходит компактный числовой JSON с траекториями точек — это на порядок дешевле по токенам и достаточно для анализа движения, формы кисти и скорости.
- **Клиентский оверлей landmarks отдельно от серверного распознавания.** Для мгновенной визуальной обратной связи (точки на руках, FPS) фронтенд использует MediaPipe Tasks Vision прямо в браузере (WASM) — это не требует круговой задержки до сервера. Параллельно сырые кадры всё равно идут на бэкенд, где `LandmarkDetector` на Python пересчитывает те же landmarks для отправки в Gemini — так сервер не зависит от того, что именно нарисовал браузер.
- **Ring buffer, а не накопление всех кадров.** `GestureSequenceBuffer` — это `collections.deque(maxlen=...)`, старые кадры автоматически вытесняются. Память ограничена и предсказуема при любой длительности сессии.
- **Cooldown между вызовами Gemini.** Без него при 8+ FPS буфер был бы "готов" почти на каждом кадре, что означало бы десятки запросов в секунду. Cooldown (по умолчанию 1.5с) — простая, но эффективная защита от лишних затрат и rate-limit'ов.
- **Отдельный `Translator` на каждое WebSocket-соединение.** Это единственный правильный способ изолировать состояние (буфер, язык) разных пользователей в асинхронном FastAPI-приложении без глобальных блокировок.
- **`AppController` + `CameraManager`.** Веб-версия получает кадры из браузера, но для быстрой локальной отладки CV-пайплайна без фронтенда полезен прямой доступ к веб-камере через OpenCV — тот же `Translator` работает в обоих сценариях.

## 5. Как работает MediaPipe

`LandmarkDetector` инициализирует два графа MediaPipe:
- **Hands** — до 2 рук, 21 точка на каждую (кончики и суставы пальцев, запястье).
- **Pose** — берутся только точки верхней части тела (плечи, локти, часть торса), поскольку ноги не несут информации о жестах, но лишний расчёт съедал бы CPU.

Оба графа переиспользуются между кадрами (создание нового графа на каждый кадр — самая частая ошибка в интеграциях MediaPipe, стоящая большей части производительности).

## 6. Как работает Gemini

`GeminiClient` строит промпт с системной инструкцией (роль эксперта по жестовому языку) + компактным JSON-представлением последовательности кадров, и просит модель вернуть **только JSON** (`response_mime_type: "application/json"`), который затем валидируется через Pydantic (`GestureRecognitionResult`). При сетевых сбоях — до 3 повторов с экспоненциальной задержкой (`tenacity`).

## 7. Буферизация кадров

Кольцевой буфер (`deque(maxlen=max_window)`) хранит последние N кадров. `min_window` (по умолчанию 30) — минимум для попытки распознавания, `max_window` (120) — потолок, после которого старые кадры вытесняются автоматически. Это даёт системе "скользящее окно" внимания: она всегда смотрит на самое недавнее движение, а не на всю историю сессии.

## 8. WebSocket-протокол

Одно соединение `/ws/translate` на сессию. Сообщения — JSON-конверты `{type, payload}`:
- `landmarks` (клиент → сервер) — `{frame: "data:image/jpeg;base64,..."}`
- `transcript` (сервер → клиент) — результат распознавания
- `status` (сервер → клиент) — готовность модели, смена языка
- `set_language` (клиент → сервер) — переключение языка жестов
- `error` (сервер → клиент) — ошибка (например, неподдерживаемый язык)

## 9. Озвучивание

- **Веб-версия:** `useSpeech` на фронтенде использует `SpeechSynthesisUtterance` (Web Speech API) — озвучивание происходит прямо в браузере пользователя, без нагрузки на сервер и без задержки на передачу аудио.
- **Локальная версия:** `SpeechEngine` (pyttsx3) используется только в `AppController` для десктопного запуска без браузера.

## 10. Взаимодействие Frontend ↔ Backend

Frontend отвечает за: доступ к камере, локальный оверлей landmarks, throttling кадров, отправку их по WebSocket, отображение результатов и TTS. Backend отвечает за: тяжёлые CV-вычисления, буферизацию, вызовы Gemini, персистентность истории и её экспорт. REST (`/api/history/*`) используется для всего, что не требует реального времени; WebSocket — только для потока кадров и результатов.

## 11. Планы масштабирования (заложено в архитектуре, не реализовано в MVP)

- Обучение собственной модели (TensorFlow/PyTorch/ONNX) как альтернатива Gemini — `GestureRecognizer` уже отделён от `GeminiClient`, поэтому подмена движка распознавания не потребует менять буфер или WebSocket-протокол.
- Локальное распознавание без внешнего API — тот же принцип: замена `GeminiClient` на локальный inference-класс с идентичным интерфейсом `recognize()`.
- Обратный перевод (текст → 3D-аватар) и видеоконференции — потребуют нового модуля и вне рамок текущего MVP.
