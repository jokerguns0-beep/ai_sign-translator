# AI Sign Language Translator

Веб-приложение для перевода жестового языка в текст и речь в реальном времени. Работает в браузере на компьютере и мобильных устройствах, без установки отдельного приложения.

- **Frontend:** Next.js 14 + React + TypeScript + TailwindCSS + Framer Motion
- **Backend:** FastAPI (Python, async), WebSocket-стриминг
- **Computer Vision:** OpenCV + MediaPipe (Hands + Pose)
- **AI-интерпретация жестов:** Google Gemini (мультимодальный анализ движения/траектории)
- **Озвучивание:** Web Speech API (веб) / pyttsx3 (локальный режим)

## Быстрый старт

Подробная инструкция — в [`docs/SETUP.md`](docs/SETUP.md).

```powershell
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # вставь свой GEMINI_API_KEY
uvicorn main:app --reload

# Frontend (в отдельном терминале)
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Открой `http://localhost:3000`, разреши доступ к камере — готово.

## Документация

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — структура проекта, поток данных, обоснование архитектурных решений.
- [`docs/SETUP.md`](docs/SETUP.md) — установка, конфигурация, частые ошибки.

## Статус MVP

Реализовано: захват видео, локальный оверлей landmarks, серверное распознавание рук/позы через MediaPipe, буферизация последовательностей движения, интерпретация через Gemini, WebSocket-стриминг без блокировок, история переводов с экспортом в TXT/PDF, переключение языка (РЖЯ активен, ASL/BSL — заготовки), настройки озвучивания, базовые тесты.

Не реализовано (заложено в архитектуре для будущего расширения — см. раздел 11 в ARCHITECTURE.md): собственная обученная модель (TensorFlow/PyTorch/ONNX) взамен Gemini, полностью локальное распознавание без внешнего API, поддержка нескольких людей одновременно, режим видеоконференций, обратный перевод текст → жесты через 3D-аватар.
