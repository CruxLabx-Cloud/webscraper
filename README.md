# ScrapeFlow

Web data extraction SaaS — MVP slice.
Powered by **Tavily** (search/discovery) + **Firecrawl** (deep extraction).

## Stack

- **Backend**: FastAPI (Python 3.12), `tavily-python`, `firecrawl-py`
- **Frontend**: Next.js 15 (App Router) + Tailwind + shadcn-style UI
- **Exports**: JSON / CSV (server-side conversion)

## Architecture

```
User input ──▶ FastAPI orchestrator ──┬──▶ Tavily (discover URLs)
                                      └──▶ Firecrawl (extract markdown / structured JSON)
                                              │
                                              ▼
                                     Next.js dashboard (table + exports)
```

## Project layout

```
webscrspper/
├── backend/
│   ├── app/
│   │   ├── api/routes.py            # /search /scrape /search-and-scrape /export
│   │   ├── core/config.py           # env settings
│   │   ├── schemas/jobs.py          # pydantic models
│   │   └── services/
│   │       ├── tavily_client.py     # search / discovery
│   │       ├── firecrawl_client.py  # scrape one + many (async)
│   │       ├── orchestrator.py      # composed pipeline
│   │       └── exporter.py          # JSON / CSV conversion
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   └── src/
│       ├── app/page.tsx             # dashboard (URLs / Search / Combo tabs)
│       ├── components/
│       │   ├── results-table.tsx
│       │   └── ui/                  # button, card, input, tabs, badge, textarea
│       └── lib/api.ts               # fetch wrappers + export download
├── docker-compose.yml               # backend in container
└── README.md
```

## Setup

### 1. Clone & enter

```bash
cd webscrspper
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set TAVILY_API_KEY and FIRECRAWL_API_KEY
uvicorn app.main:app --reload --port 8000
```

API now at `http://localhost:8000` · interactive docs at `/docs`.

### 3. Frontend

```bash
cd ../frontend
cp .env.local.example .env.local
npm install
npm run dev
```

App at `http://localhost:3000`.

### Docker (backend only)

```bash
cp backend/.env.example backend/.env  # add your keys
docker compose up --build
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET    | `/api/health`            | health check |
| POST   | `/api/search`            | Tavily search → ranked URL list |
| POST   | `/api/scrape`            | Firecrawl on a URL list (max 100) |
| POST   | `/api/search-and-scrape` | Combined pipeline |
| POST   | `/api/export?fmt=csv\|json` | Convert results to download |

### Example

```bash
curl -X POST http://localhost:8000/api/search-and-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "query": "best open-source vector databases",
    "max_results": 5,
    "formats": ["markdown"],
    "extraction_prompt": "Extract product name and key features"
  }'
```

## Workflows the UI supports

1. **URLs tab** — paste URLs (one per line) → Firecrawl extracts markdown + optional structured JSON via prompt.
2. **Search tab** — natural-language query → Tavily returns ranked sources (no scraping).
3. **Search + Scrape tab** — query → Tavily finds top N → Firecrawl scrapes all → unified table.

Results table supports row expansion (markdown / extracted / metadata) and export to JSON/CSV.

## Notes

- API keys live only in `backend/.env`; never sent to the frontend.
- The MVP runs synchronously (request returns when extraction completes). Scheduling, persistence, billing, and auth are deliberately deferred per the product spec V1.0+ roadmap.
- Concurrency is capped per request (5 parallel Firecrawl calls). Tune in `firecrawl_client.scrape_many`.
- You are responsible for honoring `robots.txt` and the ToS of sites you scrape.

## Deploy

### Frontend → Vercel

1. Import repo `HyperWrike/scrapeflow` in Vercel.
2. **Root Directory** → `frontend`
3. **Framework Preset** → Next.js (auto-detected)
4. **Environment Variables** → set `NEXT_PUBLIC_API_URL` to your deployed backend URL.
5. Deploy.

### Backend → any Python host

Vercel does not host long-running Python apps well; pick one:

- **Railway / Render / Fly.io** — point at `/backend`, run `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Docker** — `cd backend && docker build -t scrapeflow-api . && docker run -p 8000:8000 --env-file .env scrapeflow-api`.

Set environment variables in your host:
```
TAVILY_API_KEY=...
FIRECRAWL_API_KEY=...
CORS_ORIGINS=https://scrapeflow.vercel.app
```

After backend is live, update `NEXT_PUBLIC_API_URL` in Vercel and redeploy the frontend.

## Next steps (per spec)

- [ ] Postgres + job persistence
- [ ] Celery + Redis for async/scheduled jobs
- [ ] Auth (Clerk/Supabase) + workspaces
- [ ] Stripe metered billing (credit model)
- [ ] Webhook delivery
- [ ] Visual selector / AI auto-schema
