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
SERVER_HOST = os.getenv("MCP_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("MCP_PORT", "8000"))
TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

OVERLEAF_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
OVERLEAF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
