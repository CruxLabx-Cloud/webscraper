# Company Intelligence Tracker

Production-ready company research SaaS — Search one company and get a structured brief with leadership, live job postings, and digest-ready signals. Powered by **Tavily** for discovery + **Firecrawl** for structured extraction.

## Features

- **Company search**: Search a company name and resolve the best match
- **Leadership intelligence**: Surface C-suite and key decision makers with LinkedIn links
- **Multi-platform job aggregation**: Pull live hiring signals from Naukri, LinkedIn, Indeed, Foundit, and WorkIndia
- **Company watchlist**: Track companies and manage digest cadence
- **Email digests**: Send scheduled updates only when new signals appear
- **Exportable briefs**: Open a company detail page and review or share the brief
- **Production-ready**: Full error handling, security hardening, and monitoring
- **Fully containerized**: Docker and docker-compose ready

## Tech Stack

- **Backend**: FastAPI 0.115 (Python 3.12), SQLAlchemy async, Tavily + Firecrawl APIs
- **Frontend**: Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn-style components
- **Infrastructure**: Docker, Docker Compose, GitHub Actions
- **Deployment**: Cloud-ready (supports Vercel, Azure Container Apps, etc.)

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  Company Intelligence Frontend (Next.js)              │
│  - React 19 with TypeScript                           │
│  - Real-time error handling & logging                 │
│  - Responsive Tailwind UI                             │
└─────────────────────────┬──────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼──────────────────────────────┐
│  Company Intelligence API (FastAPI)                   │
│  - CORS-enabled                                        │
│  - Request validation & sanitization                   │
│  - Async processing                                    │
└─────────────┬──────────────────┬──────────────────────┘
              │                  │
       ┌──────▼─────┐    ┌──────▼──────┐
       │  Tavily API│    │ Firecrawl API
       │ (Search)   │    │ (Extraction)
       └────────────┘    └──────────────┘
```

## Quick Start

### Prerequisites

- **Backend**: Python 3.12+
- **Frontend**: Node.js 18+
- **Docker**: Docker 20.10+ & Docker Compose 2.0+ (optional)
- **API Keys**: 
  - [Tavily API Key](https://tavily.com)
  - [Firecrawl API Key](https://firecrawl.dev)

### 1. Clone & Setup

```bash
git clone <repo-url>
cd webscrspper
```

### 2. Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys and app base URL:
#   TAVILY_API_KEY=your_key_here
#   FIRECRAWL_API_KEY=your_key_here
#   APP_BASE_URL=http://localhost:3000
#   CORS_ORIGINS=http://localhost:3000

# Run server
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000` with docs at `/docs`.

### 3. Frontend Setup

```bash
cd ../frontend
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local if needed (defaults work for local dev)

# Run dev server
npm run dev
```

App available at `http://localhost:3000`.

### 4. Using Docker (Recommended)

```bash
# Setup environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys and app URL

# Build and run
docker compose up --build

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API docs: http://localhost:8000/docs
```

## Development

### Available Scripts

**Frontend:**
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Check TypeScript types
npm run test         # Run unit tests
npm run test:watch   # Run tests in watch mode
npm run test:coverage # Generate coverage report
npm run format       # Format code with Prettier
npm run analyze      # Analyze bundle size
```

**Backend:**
```bash
uvicorn app.main:app --reload  # Development
pytest                           # Run tests
black app/                      # Format code
```

### Code Quality

- **TypeScript**: Strict mode enabled
- **Linting**: ESLint with Next.js config
- **Formatting**: Prettier
- **Testing**: Jest + React Testing Library (frontend), pytest (backend)
- **Type Safety**: 100% type coverage target

## API Reference

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: Your deployment URL

### Endpoints

#### Health Check
```
GET /api/health
```
Returns: `{ "status": "ok" }`

#### Search (Tavily)
```
POST /api/search
Content-Type: application/json

{
  "query": "string (required)",
  "max_results": number (1-50, default: 10),
  "search_depth": "basic" | "advanced" (default: "basic"),
  "include_domains": string[] (optional),
  "exclude_domains": string[] (optional)
}
```

Returns: 
```json
{
  "query": "string",
  "results": [
    {
      "url": "string",
      "title": "string",
      "content": "string",
      "score": number
    }
  ]
}
```

#### Scrape URLs (Firecrawl)
```
POST /api/scrape
Content-Type: application/json

{
  "urls": string[] (required, min 1, max 100),
  "formats": ("markdown" | "html" | "links")[] (default: ["markdown"]),
  "only_main_content": boolean (default: true),
  "extraction_schema": object (optional, JSON schema),
  "extraction_prompt": string (optional, natural language)
}
```

Returns:
```json
{
  "total": number,
  "succeeded": number,
  "failed": number,
  "results": [
    {
      "url": "string",
      "success": boolean,
      "markdown": "string (optional)",
      "html": "string (optional)",
      "links": string[] (optional),
      "metadata": object,
      "extracted": object (optional),
      "error": "string (optional)"
    }
  ]
}
```

#### Search + Scrape (Combined Pipeline)
```
POST /api/search-and-scrape
Content-Type: application/json

{
  "query": "string (required)",
  "max_results": number (1-20, default: 5),
  "formats": ("markdown" | "html" | "links")[] (default: ["markdown"]),
  "extraction_schema": object (optional),
  "extraction_prompt": string (optional)
}
```

Returns:
```json
{
  "query": "string",
  "sources": [...SearchResultItem[]],
  "scraped": {...ScrapeResponse}
}
```

#### Export Results
```
POST /api/export?fmt=json|csv
Content-Type: application/json

{
  "items": object[]
}
```

Returns: Downloadable file (attachment)

## Environment Variables

### Frontend (.env.local)

```bash
# API endpoint
NEXT_PUBLIC_API_URL=http://localhost:8000

# Debug mode (true/false)
NEXT_PUBLIC_DEBUG=false

# API timeout in milliseconds
NEXT_PUBLIC_API_TIMEOUT=30000

# Max upload size in bytes
NEXT_PUBLIC_MAX_UPLOAD_SIZE=104857600

# Optional analytics
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

### Backend (.env)

```bash
# API Keys (required)
TAVILY_API_KEY=your_tavily_key
FIRECRAWL_API_KEY=your_firecrawl_key

# CORS configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Optional
LOG_LEVEL=info
```

## Deployment

### Docker Compose (Recommended for Local/Staging)

```bash
docker compose up --build
```

This starts both backend and frontend with proper networking.

### Docker (Individual Services)

**Backend:**
```bash
cd backend
docker build -t scrapeflow-backend .
docker run -p 8000:8000 \
  -e TAVILY_API_KEY=xxx \
  -e FIRECRAWL_API_KEY=xxx \
  scrapeflow-backend
```

**Frontend:**
```bash
docker build -t scrapeflow-frontend ./frontend
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://backend:8000 \
  scrapeflow-frontend
```

### Cloud Deployment

#### Azure Container Apps
```bash
# Using the generated Bicep/Terraform from appmod_get_plan
az containerapp create --resource-group myapp-rg \
  --name scrapeflow-frontend \
  --image scrapeflow-frontend:latest \
  --environment myenv
```

#### Vercel (Frontend Only)
```bash
vercel deploy --prod
```

#### AWS/GCP/Other Clouds
Use the provided Docker images for deployment on any Kubernetes-compatible platform.

## Security

### Implemented Measures

- **Input Validation**: URL validation, query length limits, max request sizes
- **XSS Protection**: React's built-in escaping, strict CSP headers
- **CSRF Protection**: SameSite cookies, origin validation
- **Security Headers**: 
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Referrer-Policy: strict-origin-when-cross-origin
- **Error Handling**: Safe error messages (no sensitive data leakage)
- **Logging**: Structured logging with privacy-conscious defaults
- **Dependencies**: Regular npm audit, dependency scanning
- **Network**: HTTPS in production, secure API communication

### Best Practices

1. **Never commit API keys** — use `.env` files with `.gitignore`
2. **Validate all inputs** — both frontend and backend
3. **Use HTTPS** — always in production
4. **Monitor logs** — watch for unusual patterns
5. **Update dependencies** — run `npm audit` regularly
6. **Rotate credentials** — API keys and secrets regularly

## Testing

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Watch mode for development
npm test --watch

# Coverage report
npm test --coverage
```

Test files are located in `src/__tests__/` and follow the naming convention `*.test.ts(x)`.

### Manual Testing Checklist

- [ ] Search with various queries
- [ ] Scrape single and multiple URLs
- [ ] Run search + scrape pipeline
- [ ] Export results as JSON
- [ ] Export results as CSV
- [ ] Verify responsive design on mobile
- [ ] Test error handling (invalid URLs, API errors)
- [ ] Test extraction prompts
- [ ] Verify API timeout handling

## Troubleshooting

### Common Issues

**Frontend can't connect to backend**
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify backend is running: `curl http://localhost:8000/api/health`
- Check CORS configuration in `backend/.env`

**API returns 429 (Rate Limited)**
- Tavily/Firecrawl rate limits hit
- Wait before retrying
- Consider upgrading plan or caching results

**Docker build fails**
- Ensure Docker daemon is running
- Check disk space: `docker system prune`
- Try: `docker build --no-cache .`

**Tests fail on first run**
- Run `npm install` in the respective directory
- Ensure Node.js version >= 18

## Performance Optimization

### Frontend
- **Code Splitting**: Automatic with Next.js App Router
- **Image Optimization**: Off (no images currently)
- **Caching**: Server-side and client-side with SWR
- **Bundle Analysis**: Run `npm run analyze`

### Backend
- **Async Processing**: All I/O operations are async
- **Connection Pooling**: Managed by httpx
- **Caching**: Implement for repeated searches (future)

### Database (Future)
- Add Redis for caching search results
- PostgreSQL for job history/analytics

## Monitoring & Analytics

### Implemented
- Client-side error logging with structured format
- Server-side request logging (FastAPI)
- Browser console in debug mode

### Recommended Additions
- Sentry for error tracking
- DataDog or New Relic for APM
- PostHog for product analytics
- CloudWatch/Azure Monitor for infrastructure

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please ensure:
- Code passes linting: `npm run lint`
- Types are correct: `npm run type-check`
- Tests pass: `npm test`

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/scrapeflow/issues)
- Email: support@scrapeflow.dev
- Documentation: [Read the docs](https://docs.scrapeflow.dev)

## Roadmap

- [ ] User authentication & accounts
- [ ] Job history & scheduling
- [ ] Advanced extraction schemas
- [ ] Proxy support for scraping
- [ ] Webhook notifications
- [ ] GraphQL API
- [ ] Mobile app
- [ ] Integration marketplace

---

Built with ❤️ for data extraction


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
