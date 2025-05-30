from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import subprocess
import json
import os
import sys
from datetime import datetime
import logging
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SCRAPER_SCRIPT_PATH = "scraper.py"  # Path to your Python scraping script
DATA_CACHE_FILE = "results.json"
CACHE_DURATION = 300  # Cache for 5 minutes (300 seconds)

class DataCache:
    def __init__(self):
        self.cache_file = DATA_CACHE_FILE
        self.cache_duration = CACHE_DURATION
    
    def is_cache_valid(self):
        """Check if cache exists and is still valid"""
        if not os.path.exists(self.cache_file):
            return False
        
        cache_time = os.path.getmtime(self.cache_file)
        current_time = datetime.now().timestamp()
        
        return (current_time - cache_time) < self.cache_duration
    
    def get_cached_data(self):
        """Get data from cache if valid"""
        if self.is_cache_valid():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        return None
    
    def save_to_cache(self, data):
        """Save data to cache"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")

cache = DataCache()

def run_scraper_script(tags=None, keyword=None, limit=50):
    """
    Run your Python scraping script and return the results
    Modify this function based on how your script accepts parameters
    """
    try:
        # Build command to run your scraper
        cmd = [sys.executable, SCRAPER_SCRIPT_PATH]
        
        # Add parameters based on your script's interface
        if tags:
            cmd.extend(['--tags', tags])
        if keyword:
            cmd.extend(['--keyword', keyword])
        if limit:
            cmd.extend(['--limit', str(limit)])
        
        logger.info(f"Running scraper with command: {' '.join(cmd)}")
        
        # Run the scraper script
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Scraper failed with error: {result.stderr}")
            return None, f"Scraper error: {result.stderr}"
        
        # Parse the output - assuming your script outputs JSON
        try:
            with open("results.json", "r") as file:
                data = json.load(file)
            return data, None
        except json.JSONDecodeError:
            # If your script doesn't output JSON, handle accordingly
            logger.error("Scraper output is not valid JSON")
            return None, "Invalid JSON output from scraper"
            
    except subprocess.TimeoutExpired:
        logger.error("Scraper script timed out")
        return None, "Scraper timed out"
    except FileNotFoundError:
        logger.error(f"Scraper script not found: {SCRAPER_SCRIPT_PATH}")
        return None, f"Scraper script not found: {SCRAPER_SCRIPT_PATH}"
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        return None, f"Error running scraper: {str(e)}"

@app.route('/api/scrape', methods=['GET', 'POST'])
def scrape_data():
    """
    Main endpoint to scrape data from GateOverflow
    Accepts both GET and POST requests
    """
    try:
        # Get parameters from request
        if request.method == 'POST':
            data = request.get_json() or {}
            tags = data.get('tags', '')
            keyword = data.get('keyword', '')
            limit = data.get('limit', 50)
            force_refresh = data.get('force_refresh', False)
        else:
            tags = request.args.get('tags', '')
            keyword = request.args.get('keyword', '')
            limit = int(request.args.get('limit', 50))
            force_refresh = request.args.get('force_refresh', '').lower() == 'true'
        
        # Check cache first (unless force refresh is requested)
        if not force_refresh:
            cached_data = cache.get_cached_data()
            if cached_data:
                logger.info("Returning cached data")
                return jsonify({
                    'success': True,
                    'data': cached_data,
                    'cached': True,
                    'message': 'Data retrieved from cache'
                })
        
        # Run the scraper
        logger.info(f"Running scraper with tags='{tags}', keyword='{keyword}', limit={limit}")
        scraped_data, error = run_scraper_script(tags, keyword, limit)
        
        if error:
            return jsonify({
                'success': False,
                'error': error,
                'message': 'Failed to scrape data'
            }), 500
        
        if not scraped_data:
            return jsonify({
                'success': False,
                'data': [],
                'message': 'No data returned from scraper'
            })
        
        # Save to cache
        cache.save_to_cache(scraped_data)
        
        return jsonify({
            'success': True,
            'data': scraped_data,
            'cached': False,
            'count': len(scraped_data) if isinstance(scraped_data, list) else 1,
            'message': f'Successfully scraped {len(scraped_data) if isinstance(scraped_data, list) else 1} items'
        })
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get API status and cache information"""
    cache_valid = cache.is_cache_valid()
    cache_exists = os.path.exists(cache.cache_file)
    
    status_info = {
        'api_status': 'running',
        'scraper_script': SCRAPER_SCRIPT_PATH,
        'scraper_exists': os.path.exists(SCRAPER_SCRIPT_PATH),
        'cache': {
            'exists': cache_exists,
            'valid': cache_valid,
            'file': cache.cache_file
        }
    }
    
    if cache_exists:
        try:
            cache_time = os.path.getmtime(cache.cache_file)
            status_info['cache']['last_updated'] = datetime.fromtimestamp(cache_time).isoformat()
        except:
            pass
    
    return jsonify(status_info)

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear the data cache"""
    try:
        if os.path.exists(cache.cache_file):
            os.remove(cache.cache_file)
            return jsonify({
                'success': True,
                'message': 'Cache cleared successfully'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Cache was already empty'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to clear cache'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    # Check if scraper script exists
    if not os.path.exists(SCRAPER_SCRIPT_PATH):
        logger.warning(f"Scraper script not found: {SCRAPER_SCRIPT_PATH}")
        print(f"⚠️  Warning: Scraper script '{SCRAPER_SCRIPT_PATH}' not found!")
        print("   Please make sure your Python scraping script is in the same directory")
        print("   or update the SCRAPER_SCRIPT_PATH variable in this file.")
    
    print("🚀 Starting Flask API server...")
    print("📊 Endpoints available:")
    print("   GET/POST /api/scrape - Run scraper and get data")
    print("   GET /api/status - Get API status")
    print("   POST /api/clear-cache - Clear data cache")
    print("   GET /health - Health check")
    
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=sys.argv[1],
        threaded=True
    )