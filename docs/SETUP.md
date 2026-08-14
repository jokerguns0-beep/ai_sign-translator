# Установка и запуск (Windows / PyCharm)

## 1. Backend

### 1.1 Создание виртуального окружения

Открой терминал в PyCharm (или PowerShell) в папке `backend/`:

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
```

Если Windows ругается на execution policy при активации venv:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 1.2 Установка зависимостей

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> На Python 3.14 иногда `mediapipe` ещё не публикует готовые wheel-пакеты в первые недели после релиза Python. Если `pip install mediapipe` падает с ошибкой сборки — поставь Python 3.11 или 3.12 через отдельный venv специально для этого проекта (`py -3.11 -m venv venv`), это самый надёжный вариант для MediaPipe на сегодня.

### 1.3 Настройка `.env`

```powershell
copy .env.example .env
```

Открой `.env` и вставь свой Gemini API-ключ (как получить — см. раздел 3 ниже).

### 1.4 Запуск

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Проверка: открой `http://localhost:8000/api/health` — должен вернуться `{"status": "ok"}`.

### 1.5 (Опционально) Локальный запуск без браузера

```powershell
python -m services.app_controller
```

Откроется окно с веб-камерой, распознанный текст будет озвучен через pyttsx3. Выход — клавиша `q`.

## 2. Frontend

### 2.1 Установка Node.js

Скачай LTS-версию с [nodejs.org](https://nodejs.org) (подойдёт 20.x). Проверь установку:

```powershell
node -v
npm -v
```

### 2.2 Установка зависимостей

```powershell
cd frontend
npm install
```

### 2.3 Настройка `.env.local`

```powershell
copy .env.local.example .env.local
```

По умолчанию там уже прописан адрес локального бэкенда — менять не нужно, если бэкенд запущен на порту 8000.

### 2.4 Запуск

```powershell
npm run dev
```

Открой `http://localhost:3000` в браузере, разреши доступ к камере.

## 3. Получение Gemini API-ключа

1. Зайди на [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Войди с Google-аккаунтом.
3. Нажми "Create API key", выбери или создай проект.
4. Скопируй ключ и вставь в `backend/.env` как `GEMINI_API_KEY`.

Бесплатный тир имеет лимиты по запросам в минуту — для разработки и демо этого достаточно; для продакшена потребуется платный тариф.

## 4. Тестирование камеры

- Если браузер показывает чёрный экран вместо видео — проверь, что сайт открыт по `http://localhost:3000` (не по IP без порта) и что в настройках браузера камера не заблокирована для этого сайта.
- На Windows проверь, что камеру не удерживает другое приложение (Zoom, OBS, Skype) — MediaPipe/getUserMedia не может работать с занятым устройством.
- Индикатор FPS и "рук в кадре" в верхнем левом углу видео помогает быстро понять, работает ли клиентское отслеживание рук.

## 5. Частые ошибки и решения

| Ошибка | Причина | Решение |
|---|---|---|
| `ModuleNotFoundError: No module named 'mediapipe'` | venv не активирован или mediapipe не поставился | активируй venv (`venv\Scripts\activate`), проверь версию Python (см. 1.2) |
| WebSocket сразу закрывается с кодом 1011 | Не задан `GEMINI_API_KEY` или неверный ключ | проверь `.env`, перезапусти `uvicorn` |
| Камера в браузере не активируется | Сайт открыт не по `localhost`/`https` | `getUserMedia` требует secure context — используй `localhost`, не `127.0.0.1` без порта или голый IP |
| `CORS` ошибка в консоли браузера | `CORS_ORIGINS` в `.env` бэкенда не совпадает с адресом фронтенда | пропиши точный адрес, например `http://localhost:3000` |
| Текст не озвучивается | Браузер не поддерживает `speechSynthesis` или голоса ещё не загрузились | обнови страницу; Chrome/Edge поддерживают Web Speech API "из коробки" |
| Распознавание работает, но текст не осмысленный | Free-tier Gemini модель менее точна, либо освещение/ракурс мешают трекингу рук | попробуй `gemini-1.5-pro` вместо `flash`, улучши освещение, держи руки в кадре полностью |

## 6. Запуск тестов

```powershell
cd backend
pytest -v
```
