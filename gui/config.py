# Configuration file for Web Scraper GUI

# AWS Lambda Configuration
LAMBDA_ENDPOINT = "EnterEndpointHere"

# GUI Configuration
WINDOW_TITLE = "Web Scraper Tool"
WINDOW_SIZE = "800x600"
MIN_WINDOW_SIZE = "600x500"

# Colors
COLORS = {
    'bg': '#f0f0f0',
    'fg': '#333333',
    'accent': '#0078d4',
    'success': '#107c10',
    'error': '#d13438',
    'warning': '#ff8c00'
}

# Timeouts
REQUEST_TIMEOUT = 60  # seconds
MAX_RETRIES = 3

# File Configuration
DEFAULT_DOWNLOAD_DIR = "./downloads"
CSV_ENCODING = 'utf-8'

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "web_scraper.log"