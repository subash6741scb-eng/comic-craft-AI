from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# The supplied document specifies Gemini Flash + Gemini Pro.
# These defaults use currently available Gemini model IDs; they can be changed in .env.
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.8-flash")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-3.1-pro-preview")

# The supplied document specifies Stable Diffusion via Hugging Face Diffusers.
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "diffusers").lower()
SD_MODEL_ID = os.getenv("SD_MODEL_ID", "runwayml/stable-diffusion-v1-5")
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

NUM_PANELS = int(os.getenv("NUM_PANELS", "5"))
IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "512"))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "512"))

PANELS_DIR = BASE_DIR / "static" / "panels"
EXPORTS_DIR = BASE_DIR / "static" / "exports"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

for folder in (PANELS_DIR, EXPORTS_DIR):
    folder.mkdir(parents=True, exist_ok=True)

EXPORT_DIR = BASE_DIR / "static" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)