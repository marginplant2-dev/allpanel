# SportX — User Frontend

Premium dark UI for end users. Vite + React + TypeScript + Tailwind + shadcn/ui.

## Setup

```powershell
cd frontend-user
npm install
Copy-Item .env.example .env
npm run dev
```

Runs on <http://localhost:5173>. API requests to `/api` are proxied to the backend at
`http://localhost:8000` during development (see `vite.config.ts`); the API base URL is
configured via `VITE_API_BASE_URL`.

## Scripts

- `npm run dev` — start dev server
- `npm run build` — type-check and build for production
- `npm run typecheck` — type-check only
- `npm run preview` — preview the production build

## Structure

```
src/
├── api/          axios client + per-resource API modules
├── components/   ui/ (shadcn primitives), common/, layout/, game/, event/, wallet/
├── features/     page-level features (landing, auth, home, sports, casino, wallet, ...)
├── hooks/        reusable hooks
├── lib/          utils, query client
├── store/        zustand stores
└── types/        shared TypeScript types
```
