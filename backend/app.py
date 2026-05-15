"""
CardosoX Scraper - Flask Backend
Production-ready web scraping API with anti-bot features
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from scraper import WebScraper
from utils import validate_urls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()

# Initialize Flask app
app = Flask(__name__)


def _parse_origins(origins_value: str):
    """Parse CORS origins from comma-separated env var."""
    if not origins_value:
        return '*'
    origins = [origin.strip() for origin in origins_value.split(',') if origin.strip()]
    return origins or '*'


CORS(app, resources={r"/api/*": {"origins": _parse_origins(os.getenv('CORS_ORIGINS', ''))}})

# Initialize scraper
scraper = WebScraper()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'CardosoX Scraper API'
    }), 200


@app.route('/api/scrape', methods=['POST'])
def scrape_urls():
    """
    Main scraping endpoint
    
    Expected POST body:
    {
        "urls": ["https://example.com", "https://another-site.com"]
    }
    
    Returns:
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
    """
    try:
        data = request.get_json(silent=True)
        
        if not data or 'urls' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing "urls" in request body'
            }), 400
        
        urls = data.get('urls', [])
        
        # Validate URLs
        validation_result = validate_urls(urls)
        if not validation_result['valid']:
            return jsonify({
                'status': 'error',
                'message': validation_result['message']
            }), 400
        
        valid_urls = validation_result.get('valid_urls', [])
        logger.info(f"Starting scrape for {len(valid_urls)} URLs")
        
        # Perform scraping
        results = scraper.scrape_multiple_urls(valid_urls)
        
        logger.info(f"Completed scraping {len(results)} URLs")
        
        # Format and return response
        return jsonify({
            'status': 'success',
            'results': results,
            'timestamp': datetime.now().isoformat(),
            'count': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Scraping failed: {str(e)}'
        }), 500


@app.route('/api/scrape/single', methods=['POST'])
def scrape_single_url():
    """
    Scrape a single URL
    
    Expected POST body:
    {
        "url": "https://example.com"
    }
    """
    try:
        data = request.get_json(silent=True)
        
        if not data or 'url' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing "url" in request body'
            }), 400
        
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'status': 'error',
                'message': 'URL cannot be empty'
            }), 400
        
        # Validate single URL
        validation_result = validate_urls([url])
        if not validation_result['valid']:
            return jsonify({
                'status': 'error',
                'message': validation_result['message']
            }), 400
        
        validated_url = validation_result.get('valid_urls', [url])[0]
        logger.info(f"Scraping single URL: {validated_url}")

        result = scraper.scrape_url(validated_url)
        
        return jsonify({
            'status': 'success',
            'result': result,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Single URL scraping error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Scraping failed: {str(e)}'
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Note: For production, use a proper WSGI server like Gunicorn
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        host='0.0.0.0',
        port=int(os.getenv('API_PORT', '5000'))
    )
