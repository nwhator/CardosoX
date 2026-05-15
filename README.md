# CardosoX Scraper - Root Directory

Complete production-ready web scraping SaaS platform.

## Project Structure

```
CardosoX/
├── cardosox/                    # Frontend (Astro)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.astro      # Landing page
│   │   │   └── scraper.astro    # Scraper dashboard
│   │   ├── components/
│   │   │   ├── Navigation.astro
│   │   │   ├── HeroSection.astro
│   │   │   └── ScraperForm.astro
│   │   ├── layouts/
│   │   │   └── Layout.astro
│   │   └── styles/
│   │       └── global.css
│   ├── tailwind.config.mjs
│   ├── astro.config.mjs
│   └── package.json
│
├── backend/                     # Backend (Flask)
│   ├── app.py                   # Flask application
│   ├── scraper.py              # Web scraping logic
│   ├── utils.py                # Utility functions
│   ├── requirements.txt         # Python dependencies
│   └── README.md               # Backend documentation
│
└── cardosox_ui/                # Design reference files
    └── ...
```

## Quick Start

### Frontend Setup

```bash
cd cardosox
npm install
npm run dev
```

Access at: `http://localhost:3000`

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
# create local config
cp .env.example .env
python app.py
```

Access API at: `http://localhost:5000`

## Technology Stack

### Frontend
- **Astro** - Static site generator
- **Tailwind CSS** - Utility-first CSS
- **Vanilla JavaScript** - No frameworks
- **Material Design 3 Colors** - Premium UI design

### Backend
- **Flask** - Python web framework
- **Playwright** - Browser automation
- **BeautifulSoup4** - HTML parsing
- **cloudscraper** - Cloudflare bypass
- **fake-useragent** - User agent rotation

## Features

- ✨ Premium SaaS dashboard UI
- 🚀 Multi-URL concurrent scraping
- 🛡️ Anti-bot detection bypass
- 📊 CSV/JSON export
- 📱 Fully responsive design
- ⚡ Real-time progress tracking
- 🔄 Automatic retry logic
- 📝 Structured data extraction

## Deployment

### Frontend (Vercel)
```bash
cd cardosox
npm run build
# Deploy dist/ folder to Vercel
```

### Backend (Render/Railway/VPS)
```bash
cd backend
# Install dependencies on server
pip install -r requirements.txt
playwright install chromium

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Environment Variables

### Backend (.env)
```
FLASK_ENV=production
API_PORT=5000
SCRAPER_TIMEOUT=30
MAX_RETRIES=3
```

### Frontend (.env)
```
PUBLIC_API_URL=https://your-backend-api.com
```

The frontend uses `PUBLIC_API_URL` as the API base URL and appends `/api/scrape`.

## Validation

### Frontend
```bash
cd cardosox
npm run build
```

### Backend
```bash
cd backend
python -m py_compile app.py scraper.py utils.py
```

## API Documentation

See [backend/README.md](backend/README.md) for complete API documentation.

## License

All rights reserved.
