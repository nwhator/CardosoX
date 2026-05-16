# CardosoX Scraper - Backend

High-performance web scraping API built with Flask and Playwright.

## Installation

1. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

1. Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

## Running the Server

Development:

```bash
python app.py
```

Production:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### Health Check

```
GET /api/health
```

### Scrape Multiple URLs

```
POST /api/scrape

Request:
{
    "urls": ["https://example.com", "https://another-site.com"]
}

Response:
{
    "status": "success",
    "results": [
        {
            "source_url": "https://example.com",
            "companies": [
                {
                    "company_name": "Company Name",
                    "email": "contact@example.com",
                    "phone": "+12345678900",
                    "address": "123 Main St, City, State",
                    "website": "https://example.com",
                    "socials": ["https://linkedin.com/company/example"],
                    "source_url": "https://example.com/contact",
                    "confidence": 0.91
                }
            ],
            "quotes": [
                {
                    "company": "Company Name",
                    "title": "Starter Package",
                    "price": "$99",
                    "currency": "USD",
                    "description": "Monthly support package",
                    "source_url": "https://example.com/pricing",
                    "confidence": 0.84
                }
            ],
            "status": "success"
        }
    ],
    "timestamp": "2024-05-15T12:00:00"
}
```

### Scrape and Export CSV

```
POST /api/scrape/csv

Request:
{
    "urls": ["https://example.com"]
}

Response:
text/csv attachment containing flattened company and quote rows.
```

### Scrape Single URL

```
POST /api/scrape/single

Request:
{
    "url": "https://example.com"
}

Response:
{
    "status": "success",
    "result": {...},
    "timestamp": "2024-05-15T12:00:00"
}
```

## Features

- AI-guided discovery that prioritizes contact, about, pricing, team, company, and profile URLs
- Deep crawler with Playwright rendering, network-idle waits, scrolling, worker queue, and image/font blocking
- Entity-aware DOM block extraction with per-container GROQ resolution to reduce cross-company email/phone/address mixing
- Email extraction from mailto, regex fallback, base64 text, common obfuscations, and Cloudflare email protection
- Phone extraction from tel links, WhatsApp links, and international formats with E.164 normalization when possible
- Address, website, social, pricing, package, fee, and quote extraction attached to DOM containers
- Confidence scoring and low-confidence match logging
- JSON and CSV exporters
- Production-oriented request headers and browser resource blocking
- Retry logic with exponential backoff
- Comprehensive error handling
- CORS enabled for frontend integration

## Configuration

Create `.env` file:

```
FLASK_ENV=development
FLASK_DEBUG=True
API_PORT=5000
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant

PLAYWRIGHT_TIMEOUT=30000
MAX_CONCURRENT_PAGES=5
MAX_CRAWL_DEPTH=3
MAX_RETRIES=3
MAX_DISCOVERY_LINKS=150
MAX_CRAWL_PAGES=150
PHONE_DEFAULT_REGION=NG

ENABLE_AI_MATCHING=true
ENABLE_QUOTE_CRAWLER=true

OUTPUT_DIR=./exports
CACHE_DIR=./cache
LOG_LEVEL=INFO

CSV_EXPORT=true
JSON_EXPORT=true
```

`SCRAPER_TIMEOUT`, `SCRAPER_WORKERS`, and `CRAWL_DEPTH` are still accepted as legacy fallbacks, but new deployments should use the keys above.
