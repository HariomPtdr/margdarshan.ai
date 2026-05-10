# web-frontend

React + Vite + TailwindCSS. Indian-citizen-friendly UI with 3 languages: Hindi (हिं), English (EN), Hinglish (HG).

## Layout

- **Left (16%)**: My complaints list + new complaint button
- **Middle (50%)**: Chat with bot — voice input, send, message bubbles
- **Right (33%)**: Live pipeline view (stages, location, classification, status)

## Run

```bash
npm install
VITE_GATEWAY_URL=http://localhost:8000 npm run dev
```

Visit `http://localhost:5173`.

## i18n

Locales in `src/locales/`. Add a key in all 3 files when adding text. Default language is Hinglish.

## Voice input

Uses browser SpeechRecognition (Chrome/Edge). Hindi locale (`hi-IN`).

## Map

OpenStreetMap via Leaflet. No API key needed. For better Indian admin boundaries, swap to Mappls in production.
