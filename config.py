import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PROFILE_DIR = BASE_DIR / "browser_data"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"

OVERLEAF_PROFILE_DIR = Path(os.getenv("OVERLEAF_PROFILE_DIR", str(DEFAULT_PROFILE_DIR)))
OVERLEAF_OUTPUT_DIR = Path(os.getenv("OVERLEAF_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))
HEADLESS = os.getenv("OVERLEAF_HEADLESS", "true").lower() in ("true", "1", "yes")
# Cloud platforms (Railway, Render, Fly) inject dynamic $PORT and require binding to 0.0.0.0
IS_CLOUD = bool(os.getenv("PORT") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER"))
if IS_CLOUD:
    SERVER_HOST = "0.0.0.0"
else:
    SERVER_HOST = os.getenv("MCP_HOST", "127.0.0.1")

SERVER_PORT = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))
TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

# Full public base URL used to build clickable PDF download links.
# Railway auto-sets RAILWAY_PUBLIC_DOMAIN (e.g. "myapp.up.railway.app").
# You can also set PUBLIC_URL explicitly (e.g. "https://myapp.up.railway.app").
_railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
_explicit_url = os.getenv("PUBLIC_URL", "")
if _explicit_url:
    PUBLIC_URL = _explicit_url.rstrip("/")
elif _railway_domain:
    PUBLIC_URL = f"https://{_railway_domain}"
elif not IS_CLOUD:
    PUBLIC_URL = f"http://127.0.0.1:{SERVER_PORT}"
else:
    PUBLIC_URL = ""  # fallback: server.py derives URL from request.base_url

OVERLEAF_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
OVERLEAF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
