import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import (
    IMAGE_PROVIDER,
    SD_MODEL_ID,
    HF_TOKEN,
    PANELS_DIR,
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
)

_pipe = None


def _safe_filename(text: str) -> str:
    """Create a safe filename from text."""
    text = str(text or "panel")
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", text)
    cleaned = cleaned.strip("_")
    return cleaned[:70] or "panel"


def _get_font(size: int):
    """Load a common Windows font, with fallback."""
    font_paths = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass

    return ImageFont.load_default()


def _create_placeholder(
    prompt: str,
    panel_number: int,
    title: str = "",
) -> Path:
    """
    Create a simple comic-style placeholder image.

    The image is saved inside static/panels.
    """

    PANELS_DIR.mkdir(parents=True, exist_ok=True)

    filename = (
        f"panel_{panel_number}_"
        f"{_safe_filename(title or 'comic')}.png"
    )

    output_path = PANELS_DIR / filename

    # Create image
    image = Image.new(
        "RGB",
        (IMAGE_WIDTH, IMAGE_HEIGHT),
        "#eef3ff",
    )

    draw = ImageDraw.Draw(image)

    # Fonts
    title_font = _get_font(32)
    panel_font = _get_font(26)
    body_font = _get_font(18)

    # Border
    margin = 18

    draw.rounded_rectangle(
        [
            margin,
            margin,
            IMAGE_WIDTH - margin,
            IMAGE_HEIGHT - margin,
        ],
        radius=20,
        outline="#222222",
        width=5,
        fill="#ffffff",
    )

    # Header
    header_height = 75

    draw.rounded_rectangle(
        [
            margin,
            margin,
            IMAGE_WIDTH - margin,
            margin + header_height,
        ],
        radius=16,
        fill="#dce7ff",
    )

    # Panel number
    panel_text = f"PANEL {panel_number}"

    draw.text(
        (40, 38),
        panel_text,
        font=panel_font,
        fill="#111111",
    )

    # Title
    title_text = str(title or "Comic Panel")

    title_box = draw.textbbox(
        (0, 0),
        title_text,
        font=title_font,
    )

    title_width = title_box[2] - title_box[0]

    draw.text(
        (
            max(40, IMAGE_WIDTH - title_width - 40),
            35,
        ),
        title_text[:35],
        font=title_font,
        fill="#111111",
    )

    # Comic illustration area
    cx = IMAGE_WIDTH // 2
    cy = 260

    # Sun / light
    draw.ellipse(
        [
            cx - 90,
            cy - 90,
            cx + 90,
            cy + 90,
        ],
        fill="#ffd966",
        outline="#333333",
        width=4,
    )

    # Character head
    head_x = cx
    head_y = 420

    draw.ellipse(
        [
            head_x - 70,
            head_y - 70,
            head_x + 70,
            head_y + 70,
        ],
        fill="#f4b183",
        outline="#222222",
        width=4,
    )

    # Eyes
    draw.ellipse(
        [
            head_x - 35,
            head_y - 20,
            head_x - 20,
            head_y - 5,
        ],
        fill="#111111",
    )

    draw.ellipse(
        [
            head_x + 20,
            head_y - 20,
            head_x + 35,
            head_y - 5,
        ],
        fill="#111111",
    )

    # Smile
    draw.arc(
        [
            head_x - 30,
            head_y,
            head_x + 30,
            head_y + 40,
        ],
        start=10,
        end=170,
        fill="#222222",
        width=4,
    )

    # Body
    draw.rounded_rectangle(
        [
            head_x - 85,
            head_y + 65,
            head_x + 85,
            head_y + 170,
        ],
        radius=20,
        fill="#8faadc",
        outline="#222222",
        width=4,
    )

    # Speech bubble
    bubble_x1 = 70
    bubble_y1 = 125
    bubble_x2 = 390
    bubble_y2 = 215

    draw.rounded_rectangle(
        [
            bubble_x1,
            bubble_y1,
            bubble_x2,
            bubble_y2,
        ],
        radius=20,
        fill="white",
        outline="#222222",
        width=3,
    )

    draw.polygon(
        [
            (bubble_x2 - 50, bubble_y2),
            (bubble_x2 - 20, bubble_y2 + 35),
            (bubble_x2 - 80, bubble_y2),
        ],
        fill="white",
        outline="#222222",
    )

    bubble_text = "ComicCraft!"

    draw.text(
        (110, 155),
        bubble_text,
        font=body_font,
        fill="#111111",
    )

    # Bottom information
    description = str(prompt or "AI generated comic panel")

    # Keep placeholder text short
    description = description.replace("\n", " ")
    description = description[:90]

    draw.text(
        (45, IMAGE_HEIGHT - 100),
        description,
        font=body_font,
        fill="#333333",
    )

    # Save
    image.save(
        output_path,
        format="PNG",
    )

    return output_path


def _load_diffusers():
    """Load Stable Diffusion only when requested."""
    global _pipe

    if _pipe is not None:
        return _pipe

    import torch
    from diffusers import StableDiffusionPipeline

    kwargs = {}

    if HF_TOKEN:
        kwargs["token"] = HF_TOKEN

    dtype = (
        torch.float16
        if torch.cuda.is_available()
        else torch.float32
    )

    _pipe = StableDiffusionPipeline.from_pretrained(
        SD_MODEL_ID,
        torch_dtype=dtype,
        **kwargs,
    )

    if torch.cuda.is_available():
        _pipe = _pipe.to("cuda")

    return _pipe


def generate_image(
    prompt: str,
    panel_number: int = 1,
    title: str = "",
) -> str:
    """
    Generate a comic panel image.

    Returns a browser-accessible URL such as:
        /static/panels/panel_1_comic.png
    """

    PANELS_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    # PLACEHOLDER MODE
    # -------------------------------------------------
    if IMAGE_PROVIDER.lower() == "placeholder":
        output_path = _create_placeholder(
            prompt=prompt,
            panel_number=panel_number,
            title=title,
        )

    # -------------------------------------------------
    # STABLE DIFFUSION MODE
    # -------------------------------------------------
    elif IMAGE_PROVIDER.lower() in {
        "diffusers",
        "stable-diffusion",
        "stable_diffusion",
    }:

        pipe = _load_diffusers()

        enhanced_prompt = (
            "comic book illustration, colorful, clean line art, "
            "expressive characters, cinematic composition, "
            f"{prompt}"
        )

        result = pipe(
            enhanced_prompt,
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            num_inference_steps=25,
        )

        image = result.images[0]

        filename = (
            f"panel_{panel_number}_"
            f"{_safe_filename(title or 'comic')}.png"
        )

        output_path = PANELS_DIR / filename

        image.save(output_path)

    else:
        raise ValueError(
            f"Unsupported IMAGE_PROVIDER: {IMAGE_PROVIDER}. "
            "Use 'placeholder' or 'diffusers'."
        )

    # IMPORTANT:
    # Return a URL, not a Windows filesystem path.
    return "/static/panels/" + output_path.name