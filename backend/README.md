# CardosoX Scraper - Backend

High-performance web scraping API built with Flask and Playwright.

## Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
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
            "url": "https://example.com",
            "company_name": "Company Name",
            "emails": ["contact@example.com"],
            "phone_numbers": ["+1-234-567-8900"],
            "addresses": ["123 Main St, City, State"],
            "status": "success"
        }
    ],
    "timestamp": "2024-05-15T12:00:00"
}
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

- Concurrent multi-URL scraping
- Anti-bot detection bypass (Playwright stealth mode)
- Cloudflare bypass (cloudscraper fallback)
- Automatic contact page detection
- Email, phone, and address extraction
- Random user agents and viewport sizes
- Retry logic with exponential backoff
- Comprehensive error handling
- CORS enabled for frontend integration

## Configuration

Create `.env` file:
```
FLASK_ENV=development
FLASK_DEBUG=True
API_PORT=5000
SCRAPER_TIMEOUT=30
MAX_RETRIES=3
```
