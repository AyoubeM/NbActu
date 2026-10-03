import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Settings
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SPOILER_MODE = os.getenv("SPOILER_MODE", "true").lower() in ("true", "1", "yes")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://ayoubem.github.io/NbActu/").strip()
FALLBACK_TO_US_HIGHLIGHTS = os.getenv("FALLBACK_TO_US_HIGHLIGHTS", "true").lower() in ("true", "1", "yes")
OVERRIDE_DATE = os.getenv("OVERRIDE_DATE", "").strip()

# NBA Channels & Sources
NBA_YOUTUBE_CHANNEL_ID = "UCWJ2lWNubArHWmf3FIHbfcQ"
BEIN_FR_CHANNEL_ID = "UCfj4kQ6_mYO5r4hzX5KloVw"

# Data directories
DATA_DIR = BASE_DIR / "data"
WEB_DIR = BASE_DIR / "web"
