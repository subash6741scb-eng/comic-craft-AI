import json
import re
import time

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_PRO_MODEL


_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def _extract_json(text: str):
    """Extract a JSON array from Gemini's response."""

    text = text.strip()

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
    Generate the detailed comic story.

    Uses the configured model first and automatically
    falls back to other Flash models if Gemini returns
    temporary 503/429/5xx errors.
    """

    if not _client:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    models_to_try = [
        GEMINI_PRO_MODEL,
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
        print(f"Trying Gemini story model: {model_name}")
        print("=" * 60)

        for attempt in range(max_retries + 1):

            try:

                print(
                    f"Gemini story request: "
                    f"{model_name} "
                    f"attempt {attempt + 1}/{max_retries + 1}"
                )

                response = _client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.9,
                        max_output_tokens=7000,
                    ),
                )

                print(
                    f"SUCCESS: Story generated using "
                    f"{model_name}"
                )

                return response

            except Exception as error:

                last_error = error
                error_text = str(error)

                print(
                    f"Gemini story error from "
                    f"{model_name}: {error_text}"
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

                if not retryable:
                    raise error

                if attempt < max_retries:

                    delay = 2 ** (attempt + 1)

                    print(
                        f"Temporary Gemini story error."
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

        print(
            f"Switching from {model_name} "
            f"to the next story fallback model..."
        )

    raise RuntimeError(
        "All Gemini story models are currently "
        "unavailable. "
        f"Last error: {last_error}"
    )


def generate_story(
    outline: list[dict],
    character_name: str,
    tone: str
) -> list[dict]:

    """Expand the panel outline into a complete story."""

    if not _client:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    compact_outline = json.dumps(
        outline,
        ensure_ascii=False
    )

    prompt = f"""
You are a professional comic-book writer.

Expand the following {len(outline)}-panel outline
into a coherent and engaging comic story.

Main character:
{character_name}

Tone:
{tone}

For every panel create:

- panel (integer)
- caption (short ambient/background caption)
- narration (2-4 sentences)
- dialogue (1-3 short dialogue lines)

Keep the same characters and story continuity
throughout all panels.

Do not introduce unexplained characters.

Return ONLY a valid JSON array.

Do not use markdown.
Do not use code fences.
Do not add explanations.

OUTLINE:
{compact_outline}
"""

    response = _generate_with_retry(prompt)

    story = _extract_json(
        response.text or ""
    )

    if not isinstance(story, list):
        raise ValueError(
            "Gemini did not return a valid story list."
        )

    if len(story) != len(outline):
        raise ValueError(
            f"Expected {len(outline)} story panels, "
            f"but Gemini returned {len(story)}."
        )

    required_fields = {
        "panel",
        "caption",
        "narration",
        "dialogue",
    }

    for index, panel in enumerate(
        story,
        start=1
    ):

        if not isinstance(panel, dict):
            raise ValueError(
                f"Story panel {index} is invalid."
            )

        missing = required_fields - set(panel.keys())

        if missing:
            raise ValueError(
                f"Story panel {index} is missing: "
                f"{', '.join(missing)}"
            )

        panel["panel"] = index

    return story