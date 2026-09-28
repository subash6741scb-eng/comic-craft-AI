import json
import re
import time

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_FLASH_MODEL, NUM_PANELS


_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def _extract_json(text: str):
    """Extract a JSON array from Gemini's response."""

    text = text.strip()

    # Remove markdown code fences if Gemini adds them.
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError(
            "Gemini did not return a valid JSON array."
        )

    return json.loads(text[start:end + 1])


def _generate_with_retry(prompt: str, max_retries: int = 2):
    """
    Generate content using Gemini.

    If Gemini temporarily returns 503/429/5xx errors,
    retry and then try fallback Flash models.
    """

    if not _client:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    models_to_try = [
        GEMINI_FLASH_MODEL,
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ]

    # Remove duplicate model names.
    models_to_try = list(dict.fromkeys(models_to_try))

    last_error = None

    for model_name in models_to_try:

        print()
        print("=" * 60)
        print(f"Trying Gemini model: {model_name}")
        print("=" * 60)

        for attempt in range(max_retries + 1):

            try:

                print(
                    f"Gemini request: "
                    f"{model_name} "
                    f"attempt {attempt + 1}/{max_retries + 1}"
                )

                response = _client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=5000,
                    ),
                )

                print(
                    f"SUCCESS: Gemini responded using "
                    f"{model_name}"
                )

                return response

            except Exception as error:

                last_error = error
                error_text = str(error)

                print(
                    f"Gemini error from {model_name}: "
                    f"{error_text}"
                )

                retryable = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "500" in error_text
                    or "INTERNAL" in error_text
                    or "502" in error_text
                    or "504" in error_text
                    or "DEADLINE_EXCEEDED" in error_text
                )

                # If it is not a temporary error,
                # stop immediately.
                if not retryable:
                    raise error

                # Retry the same model.
                if attempt < max_retries:

                    delay = 2 ** (attempt + 1)

                    print(
                        f"Temporary Gemini error."
                    )
                    print(
                        f"Retrying in {delay} seconds..."
                    )

                    time.sleep(delay)

                else:

                    print(
                        f"{model_name} failed after "
                        f"{max_retries + 1} attempts."
                    )

        print()
        print(
            f"Switching from {model_name} "
            f"to the next fallback model..."
        )

    raise RuntimeError(
        "All Gemini Flash models are currently "
        "unavailable. "
        f"Last error: {last_error}"
    )


def generate_outline(
    user_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str
) -> list[dict]:

    """Generate the structured comic outline."""

    if not _client:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    prompt = f"""
You are a professional AI comic planner.

Create exactly {NUM_PANELS} connected comic panels.

User story idea:
{user_prompt}

Main character:
{character_name}

Setting:
{setting}

Tone:
{tone}

Art style:
{art_style}

Return ONLY valid JSON as an array.

Each object must contain:

- panel (integer)
- title (string)
- scene_description (string)
- image_prompt (string)

The image_prompt must be a detailed visual prompt
suitable for Stable Diffusion.

Keep the same character appearance and visual
continuity across all panels.

Do not include markdown, commentary,
or code fences.
"""

    response = _generate_with_retry(prompt)

    panels = _extract_json(
        response.text or ""
    )

    if not isinstance(panels, list):
        raise ValueError(
            "Gemini did not return a list of panels."
        )

    if len(panels) != NUM_PANELS:
        raise ValueError(
            f"Expected {NUM_PANELS} panels, "
            f"but Gemini returned {len(panels)}."
        )

    required_fields = {
        "panel",
        "title",
        "scene_description",
        "image_prompt",
    }

    for index, panel in enumerate(
        panels,
        start=1
    ):

        if not isinstance(panel, dict):
            raise ValueError(
                f"Panel {index} is not a valid object."
            )

        missing = required_fields - set(panel.keys())

        if missing:
            raise ValueError(
                f"Panel {index} is missing: "
                f"{', '.join(missing)}"
            )

        # Make sure panel numbers are sequential.
        panel["panel"] = index

    return panels