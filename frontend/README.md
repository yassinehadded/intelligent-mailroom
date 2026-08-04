# Intelligent Mailroom UI

React + TypeScript frontend for the existing FastAPI backend.

## Stack

- Vite + React + TypeScript
- Tailwind CSS v4
- TanStack Query
- React Router
- Framer Motion
- Sonner toasts

## Prerequisites

- Node.js 20+
- FastAPI backend running on `http://localhost:8000`

## Development

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The Vite dev server proxies `/api` to `http://localhost:8000`.

## Production build

```powershell
cd frontend
npm install
npm run build
npm run preview
```

## Internationalization

English (default) and French are supported via `react-i18next`.

- Language switcher: top-right header (🌐 dropdown)
- Preference stored in `localStorage` key `mailroom-language`
- Translation files: `src/locales/{en,fr}/*.json`


| Page | Backend APIs used |
|------|-------------------|
| Dashboard | `/health/ready`, `/email/status`, `/email/health`, `/maarch/health`, `/analysis/status`, `/audit/events`, `/email/poll` |
| Email | `/email/status`, `/email/health`, `/email/poll`, `/audit/events` |
| AI | `/analysis/status`, `/analysis/routing-rules`, `/analysis/classify` |
| Documents | `/audit/events?event_type=ingested` |
| Maarch | `/maarch/connection`, `/maarch/health`, `/maarch/entities`, `/maarch/reference` |
| Settings | read-only status endpoints (no save API) |
| Logs | `/audit/events` |

## Notes

- The backend does not expose a live mailbox listing API yet. Email and document tables use audit events.
- Settings are read-only because configuration is loaded from backend `.env`.
- Worker start/stop is managed via Docker Compose, not the REST API.
