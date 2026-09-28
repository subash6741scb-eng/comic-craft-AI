import os
import re
from datetime import datetime

from fpdf import FPDF

from .config import EXPORT_DIR


def _safe_text(value) -> str:
    """Convert generated content into PDF-safe text."""

    if value is None:
        return ""

    text = str(value)

    # Replace common Unicode punctuation.
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Insert a break opportunity into extremely long
    # unbroken strings.
    text = re.sub(r"(\S{60})(?=\S)", r"\1 ", text)

    return text


def save_pdf(layout: list[dict]) -> str:
    """Create and save the final ComicCraft PDF."""

    os.makedirs(EXPORT_DIR, exist_ok=True)

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4",
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15,
    )

    # Safe margins.
    pdf.set_margins(
        left=15,
        top=15,
        right=15,
    )

    for panel in layout:

        pdf.add_page()

        # -------------------------------------------------
        # Panel title
        # -------------------------------------------------

        pdf.set_font(
            "Helvetica",
            style="B",
            size=16,
        )

        title = _safe_text(
            panel.get("title", "")
        )

        usable_width = (
            pdf.w
            - pdf.l_margin
            - pdf.r_margin
        )

        pdf.multi_cell(
            usable_width,
            9,
            title,
        )

        pdf.ln(3)

        # -------------------------------------------------
        # Panel image
        # -------------------------------------------------

        image_path = panel.get(
            "image_path"
        )

        if image_path and os.path.exists(image_path):

            image_width = min(
                usable_width,
                170,
            )

            x = (
                pdf.l_margin
                + (
                    usable_width
                    - image_width
                ) / 2
            )

            pdf.image(
                image_path,
                x=x,
                w=image_width,
            )

            pdf.ln(5)

        # -------------------------------------------------
        # Scene description
        # -------------------------------------------------

        scene_description = _safe_text(
            panel.get(
                "scene_description",
                "",
            )
        )

        if scene_description:

            pdf.set_font(
                "Helvetica",
                style="I",
                size=10,
            )

            pdf.multi_cell(
                usable_width,
                6,
                scene_description,
            )

            pdf.ln(2)

        # -------------------------------------------------
        # Caption
        # -------------------------------------------------

        caption = _safe_text(
            panel.get(
                "caption",
                "",
            )
        )

        if caption:

            pdf.set_font(
                "Helvetica",
                style="B",
                size=11,
            )

            pdf.multi_cell(
                usable_width,
                6,
                f"Caption: {caption}",
            )

            pdf.ln(1)

        # -------------------------------------------------
        # Narration
        # -------------------------------------------------

        narration = _safe_text(
            panel.get(
                "narration",
                "",
            )
        )

        if narration:

            pdf.set_font(
                "Helvetica",
                size=10,
            )

            pdf.multi_cell(
                usable_width,
                6,
                narration,
            )

            pdf.ln(2)

        # -------------------------------------------------
        # Dialogue
        # -------------------------------------------------

        dialogue = panel.get(
            "dialogue",
            [],
        )

        if dialogue:

            pdf.set_font(
                "Helvetica",
                style="B",
                size=10,
            )

            if isinstance(dialogue, list):

                dialogue_text = "\n".join(
                    _safe_text(line)
                    for line in dialogue
                    if str(line).strip()
                )

            else:

                dialogue_text = _safe_text(
                    dialogue
                )

            if dialogue_text:

                pdf.multi_cell(
                    usable_width,
                    6,
                    f"Dialogue:\n{dialogue_text}",
                )

    filename = (
        "comic_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        + ".pdf"
    )

    output_path = os.path.join(
        EXPORT_DIR,
        filename,
    )

    pdf.output(output_path)

    return output_path