# SportX — Admin Frontend

Premium SaaS admin dashboard. Vite + React + TypeScript + Tailwind + shadcn/ui +
Recharts + TanStack Table.

## Setup

```powershell
cd frontend-admin
npm install
Copy-Item .env.example .env
npm run dev
```

Runs on <http://localhost:5174>. API requests to `/api` are proxied to the backend at
`http://localhost:8000` during development; the API base URL is configured via
`VITE_API_BASE_URL`.

## Scripts

- `npm run dev` — start dev server
- `npm run build` — type-check and build for production
- `npm run typecheck` — type-check only
- `npm run preview` — preview the production build

## Structure

```
src/
├── api/          axios client + per-resource API modules
├── components/   ui/ (shadcn primitives), DataTable, FilterBar, HierarchyTree, charts/
├── features/     dashboard, users, hierarchy, credits, content, reports, system, security
├── hooks/
├── lib/
├── store/
└── types/
```
