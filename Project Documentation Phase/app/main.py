from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import router


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Static directory
STATIC_DIR = BASE_DIR / "static"

# Make sure static folders exist
(STATIC_DIR / "panels").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "exports").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    description="Generate personalized 5-panel comics with Gemini and Stable Diffusion.",
    version="1.0.0",
)

# Serve CSS, JavaScript, panel images and exported PDFs
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

# Application routes
app.include_router(router)