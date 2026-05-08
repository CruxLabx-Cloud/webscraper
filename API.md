# API Documentation

Complete API reference for ScrapeFlow backend.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.yourdomain.com`

## Authentication

Currently no authentication required. Future versions will support:
- API key authentication
- OAuth 2.0
- JWT tokens

## Response Format

All responses are JSON. Successful responses return 2xx status codes.

### Success Response

```json
{
  "data": {},
  "status": "success",
  "timestamp": "2026-04-30T12:00:00Z"
}
```

### Error Response

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "URL validation failed",
    "details": "Invalid URL: not-a-url"
  },
  "status": "error",
  "timestamp": "2026-04-30T12:00:00Z"
}
```

## Endpoints

### Health Check

Check API availability and status.

```
GET /api/health
```

**Response**
```json
{
  "status": "ok"
}
```

**Example**
```bash
curl http://localhost:8000/api/health
```

---

### Search (Tavily)

Discover URLs using Tavily search API.

```
POST /api/search
Content-Type: application/json
```

**Request Body**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `query` | string | Yes | Search query | Min 1 char, max 500 chars |
| `max_results` | integer | No | Max results to return | Default: 10, Range: 1-50 |
| `search_depth` | string | No | Search depth level | Default: "basic", Options: "basic", "advanced" |
| `include_domains` | array[string] | No | Only include these domains | Max 10 domains |
| `exclude_domains` | array[string] | No | Exclude these domains | Max 10 domains |

**Request Example**
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "best react frameworks 2026",
    "max_results": 10,
    "search_depth": "basic"
  }'
```

**Response Body**

```json
{
  "query": "best react frameworks 2026",
  "results": [
    {
      "url": "https://example.com/react-frameworks",
      "title": "Top React Frameworks 2026",
      "content": "This article explores the best React frameworks...",
      "score": 0.95
    },
    {
      "url": "https://blog.example.com/react-guide",
      "title": "React Guide",
      "content": "A comprehensive guide to React...",
      "score": 0.87
    }
  ]
}
```

**Response Codes**

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Invalid request (missing query, invalid params) |
| 429 | Rate limited |
| 500 | Server error |
| 502 | Tavily API error |

---

### Scrape URLs (Firecrawl)

Extract content from URLs.

```
POST /api/scrape
Content-Type: application/json
```

**Request Body**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `urls` | array[string] | Yes | URLs to scrape | Min 1, Max 100 |
| `formats` | array[string] | No | Output formats | Options: "markdown", "html", "links" |
| `only_main_content` | boolean | No | Extract main content only | Default: true |
| `extraction_schema` | object | No | JSON schema for extraction | Valid JSON schema |
| `extraction_prompt` | string | No | Natural language extraction instruction | Max 1000 chars |

**Request Example**
```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/article1",
      "https://example.com/article2"
    ],
    "formats": ["markdown"],
    "extraction_prompt": "Extract the main headline and date published"
  }'
```

**Response Body**

```json
{
  "total": 2,
  "succeeded": 1,
  "failed": 1,
  "results": [
    {
      "url": "https://example.com/article1",
      "success": true,
      "markdown": "# Article Title\n\nContent here...",
      "html": "<html>...</html>",
      "links": ["https://link1.com", "https://link2.com"],
      "metadata": {
        "title": "Article Title",
        "description": "Article description",
        "author": "Author Name",
        "publish_date": "2026-04-30"
      },
      "extracted": {
        "headline": "Article Title",
        "date": "2026-04-30"
      }
    },
    {
      "url": "https://example.com/article2",
      "success": false,
      "error": "Failed to fetch URL: 404 Not Found"
    }
  ]
}
```

**Response Codes**

| Code | Description |
|------|-------------|
| 200 | Partial or full success |
| 400 | Invalid request |
| 429 | Rate limited |
| 500 | Server error |
| 502 | Firecrawl API error |

---

### Search + Scrape (Combined Pipeline)

Discover and scrape in one request.

```
POST /api/search-and-scrape
Content-Type: application/json
```

**Request Body**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `query` | string | Yes | Search query | Min 1 char, max 500 chars |
| `max_results` | integer | No | URLs to discover | Default: 5, Range: 1-20 |
| `formats` | array[string] | No | Output formats | Options: "markdown", "html", "links" |
| `extraction_schema` | object | No | JSON schema for extraction | Valid JSON schema |
| `extraction_prompt` | string | No | Natural language instruction | Max 1000 chars |

**Request Example**
```bash
curl -X POST http://localhost:8000/api/search-and-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI agent frameworks comparison",
    "max_results": 5,
    "formats": ["markdown"],
    "extraction_prompt": "Extract name, features, and pricing"
  }'
```

**Response Body**

```json
{
  "query": "AI agent frameworks comparison",
  "sources": [
    {
      "url": "https://example.com/framework-comparison",
      "title": "AI Framework Comparison 2026",
      "content": "This article compares...",
      "score": 0.98
    }
  ],
  "scraped": {
    "total": 1,
    "succeeded": 1,
    "failed": 0,
    "results": [
      {
        "url": "https://example.com/framework-comparison",
        "success": true,
        "markdown": "# Comparison\n\n...",
        "metadata": { "title": "AI Framework Comparison 2026" },
        "extracted": {
          "frameworks": [
            {
              "name": "Framework A",
              "features": ["Feature 1", "Feature 2"],
              "pricing": "$99/month"
            }
          ]
        }
      }
    ]
  }
}
```

---

### Export Results

Export results as JSON or CSV.

```
POST /api/export?fmt=json|csv
Content-Type: application/json
```

**Query Parameters**

| Parameter | Type | Required | Options |
|-----------|------|----------|---------|
| `fmt` | string | Yes | "json", "csv" |

**Request Body**

```json
{
  "items": [
    {
      "url": "https://example.com",
      "title": "Example",
      "content": "..."
    }
  ]
}
```

**Request Example**

```bash
# Export as JSON
curl -X POST "http://localhost:8000/api/export?fmt=json" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"url": "https://example.com", "title": "Example"}
    ]
  }' \
  -o export.json

# Export as CSV
curl -X POST "http://localhost:8000/api/export?fmt=csv" \
  -H "Content-Type: application/json" \
  -d '{"items": [...]}' \
  -o export.csv
```

**Response**

- **Content-Type**: `application/json` or `text/csv`
- **Headers**: `Content-Disposition: attachment; filename="export.{fmt}"`
- **Body**: File contents

---

## Error Codes

### Client Errors (4xx)

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid input or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Endpoint not found |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Errors (5xx)

| Code | Name | Description |
|------|------|-------------|
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | External API error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Rate Limiting

- **Limit**: 100 requests per minute (per IP)
- **Header**: `X-RateLimit-Remaining`
- **Retry-After**: Returned when rate limited

---

## Best Practices

### 1. Input Validation

Always validate user input before sending to API:

```javascript
// Validate URLs
const isValidUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// Validate query length
const isValidQuery = (query) => query.trim().length > 0;
```

### 2. Error Handling

Implement proper error handling:

```javascript
try {
  const response = await api.search(query);
  // Handle success
} catch (error) {
  if (error.status === 429) {
    // Retry with backoff
  } else if (error.status >= 500) {
    // Retry
  } else {
    // Display error to user
  }
}
```

### 3. Rate Limiting

Implement request debouncing/throttling:

```javascript
// Debounce search input
const debouncedSearch = debounce((query) => {
  api.search(query);
}, 500);
```

### 4. Retry Strategy

Implement exponential backoff:

```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.retryable && i < maxRetries - 1) {
        await sleep(Math.pow(2, i) * 1000);
      } else {
        throw error;
      }
    }
  }
}
```

### 5. Caching

Cache search results to reduce API calls:

```javascript
const cache = new Map();

async function cachedSearch(query) {
  if (cache.has(query)) {
    return cache.get(query);
  }
  const result = await api.search(query);
  cache.set(query, result);
  return result;
}
```

---

## WebSocket Events (Future)

Real-time scraping updates (planned):

```
WS /api/scrape/ws
```

**Events**

- `scrape:start` - Scraping started
- `scrape:progress` - Progress update
- `scrape:complete` - Scraping completed
- `scrape:error` - Error occurred

---

## Changelog

### v0.1.0 (2026-04-30)
- Initial API release
- Search, Scrape, Search+Scrape endpoints
- JSON/CSV export

### v0.2.0 (Planned)
- Authentication support
- WebSocket for real-time updates
- Advanced filtering options
- Webhook notifications
