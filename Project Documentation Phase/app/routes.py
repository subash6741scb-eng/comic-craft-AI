from pathlib import Path
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from .config import EXPORTS_DIR
from .schemas import PromptRequest
from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .exporters import save_pdf

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _generate_comic(data: PromptRequest):
    outline = generate_outline(
        data.story_prompt,
        data.character_name,
        data.setting,
        data.tone,
        data.art_style,
    )
    story = generate_story(outline, data.character_name, data.tone)

    image_paths = []
    for index, panel in enumerate(outline, start=1):
        image_prompt = (
            f"{panel['image_prompt']}. "
            f"Art style: {data.art_style}. "
            "Keep character design consistent with previous panels. "
            "High-quality comic illustration, cinematic composition."
        )
        path = generate_image(image_prompt, f"panel_{index}.png")
        image_paths.append(path)

    layout = build_comic_layout(image_paths, story, outline)
    pdf_path = save_pdf(layout)

    return outline, story, layout, pdf_path


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    try:
        data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )
        outline, story, layout, pdf_path = _generate_comic(data)
        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "pdf_filename": Path(pdf_path).name,
                "request_data": data.model_dump(),
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate-comic/json")
async def generate_comic_json(data: PromptRequest):
    try:
        outline, story, layout, pdf_path = _generate_comic(data)
        public_pdf = "/exports/" + Path(pdf_path).name
        return {
            "success": True,
            "layout": layout,
            "pdf_path": public_pdf,
            "outline": outline,
            "story": story,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/download/{filename}")
async def download_pdf(filename: str):
    safe_name = Path(filename).name
    pdf_path = EXPORTS_DIR / safe_name
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF not found.")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=safe_name,
    )


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf_path: str = ""):
    filename = Path(pdf_path).name if pdf_path else ""
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={"pdf_filename": filename},
    )


@router.get("/test-image", response_class=HTMLResponse)
async def test_image(request: Request, prompt: str = "a futuristic city at sunset, comic book art"):
    try:
        image_path = generate_image(prompt, "test_image.png")
        image_url = "/" + image_path.replace("\\", "/")
        return templates.TemplateResponse(
            request=request,
            name="test_image.html",
            context={"image_url": image_url, "prompt": prompt},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
