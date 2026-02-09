import os

from dotenv import load_dotenv

# Load environment variables from .env (if present)
load_dotenv()


LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "ws://livekit:7880")
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://spring:8080")

# Optional knobs
ANALYSIS_HARD_TIMEOUT_SEC: float = float(os.getenv("ANALYSIS_HARD_TIMEOUT_SEC", "0"))
