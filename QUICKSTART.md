# Quick Start Guide

Get ScrapeFlow running in 5 minutes.

## Option 1: Local Development (Recommended)

### Prerequisites
- Node.js 18+
- Python 3.12+
- Tavily API key (free at tavily.com)
- Firecrawl API key (free at firecrawl.dev)

### Steps

**1. Backend Setup**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
```
TAVILY_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
CORS_ORIGINS=http://localhost:3000
```

Start backend:
```bash
uvicorn app.main:app --reload --port 8000
```

✅ Backend ready at `http://localhost:8000`

**2. Frontend Setup** (in new terminal)
```bash
cd frontend
npm install
npm run dev
```

✅ Frontend ready at `http://localhost:3000`

**3. Done!** Open http://localhost:3000 in your browser

## Option 2: Docker (Production-like)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Steps

**1. Configure**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

**2. Run**
```bash
docker compose up --build
```

**3. Access**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Testing

### Search for URLs
```
1. Go to "Search" tab
2. Enter query: "best react frameworks 2026"
3. Click "Search (Tavily)"
4. Wait for results
```

### Scrape URLs
```
1. Go to "URLs" tab
2. Enter URLs (one per line):
   https://github.com
   https://example.com
3. Click "Scrape URLs"
4. View results and expand for details
```

### Combined Pipeline
```
1. Go to "Search + Scrape" tab
2. Enter query: "pricing pages of leading tools"
3. Click "Search + Scrape"
4. See discovered URLs and scraped content
```

### Export Results
```
1. After scraping, results appear
2. Click "JSON" or "CSV" to download
3. File saved to your Downloads folder
```

## API Testing

### Using curl

**Health Check**
```bash
curl http://localhost:8000/api/health
```

**Search**
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "web scraping tools", "max_results": 5}'
```

**Scrape**
```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"]}'
```

## Troubleshooting

### "Connection refused" at localhost:3000/8000
- **Frontend**: `npm run dev` running in frontend directory?
- **Backend**: `uvicorn ...` running in backend directory?
- **Docker**: `docker compose up` successful?

### "API Error" in UI
- Check API key is set in `backend/.env`
- Check `CORS_ORIGINS` includes frontend URL
- Check backend logs for errors

### "Invalid URL" error
- URLs must start with `http://` or `https://`
- No spaces allowed in URLs
- Maximum 100 URLs per request

### Port already in use
**Frontend (3000)**:
```bash
npm run dev -- -p 3001  # Use different port
```

**Backend (8000)**:
```bash
uvicorn app.main:app --port 8001  # Use different port
```

**Docker**:
```bash
# Edit docker-compose.yml ports section
```

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEBUG=false
NEXT_PUBLIC_API_TIMEOUT=30000
```

### Backend (.env)
```
TAVILY_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
CORS_ORIGINS=http://localhost:3000
```

## Next Steps

1. **Explore API**: Visit http://localhost:8000/docs
2. **Read Docs**: See README.md
3. **Check API Ref**: See API.md
4. **Deploy**: See DEPLOYMENT.md
5. **Contribute**: See CONTRIBUTING.md

## Common Tasks

### Change API URL
Edit `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://your-api-url:8000
```

### Add more domains to search
Edit backend search in API endpoint:
```json
{
  "query": "...",
  "include_domains": ["github.com", "stackoverflow.com"]
}
```

### Extract structured data
Add extraction prompt:
```
"extraction_prompt": "Extract the main heading and publish date"
```

### Export in CSV format
Click "CSV" button in results section

## Get Help

- 📖 [Full Documentation](./README.md)
- 🔧 [API Reference](./API.md)
- 🚀 [Deployment Guide](./DEPLOYMENT.md)
- 🤝 [Contributing Guide](./CONTRIBUTING.md)
- 🐛 [Report Issues](https://github.com/yourusername/scrapeflow/issues)

---

Enjoy using ScrapeFlow! 🚀
