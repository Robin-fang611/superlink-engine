import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Proxy configuration
# Priority: 1. Environment variables (HTTP_PROXY/HTTPS_PROXY) 2. Hardcoded default (for local dev)
# Set USE_PROXY=False in .env or environment to disable proxy
USE_PROXY = os.getenv("USE_PROXY", "True").lower() == "true"
DEFAULT_PROXY = "http://127.0.0.1:7897"

if USE_PROXY:
    PROXY_URL = os.getenv("HTTP_PROXY") or os.getenv("http_proxy") or DEFAULT_PROXY
    
    os.environ['HTTP_PROXY'] = PROXY_URL
    os.environ['HTTPS_PROXY'] = PROXY_URL
    os.environ['http_proxy'] = PROXY_URL
    os.environ['https_proxy'] = PROXY_URL
    print(f"[Config] Proxy enabled: {PROXY_URL}")
else:
    # Explicitly clear proxy if disabled
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        if var in os.environ:
            del os.environ[var]
    print("[Config] Proxy disabled")

# Get API Keys
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")

if not SERPER_API_KEY:
    print("Warning: SERPER_API_KEY not found in .env")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in .env")
