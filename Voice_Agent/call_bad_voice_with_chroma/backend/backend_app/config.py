import os
import dotenv
from pathlib import Path

# Get the project root directory (2 levels up from this file)
ROOT_DIR = Path(__file__).parent.parent.parent
dotenv.load_dotenv(ROOT_DIR / ".env")


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
    TTS_MODEL_NAME = "eleven_monolingual_v1"  # Default model
