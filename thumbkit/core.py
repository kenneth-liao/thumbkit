import os
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional, Tuple

from importlib import resources
from google import genai
from google.genai import types as gtypes

# Model identifiers
MODEL_FLASH = "gemini-2.5-flash-image"  # Nano Banana (original)
MODEL_PRO = "gemini-3-pro-image-preview"  # Nano Banana Pro (new default)

# Default model (Pro for better quality)
DEFAULT_MODEL = "pro"
DEFAULT_SIZE = "1K"

# Model name mapping
MODEL_NAMES = {
    "flash": MODEL_FLASH,
    "pro": MODEL_PRO,
}

# Valid sizes for Pro model (Flash only supports 1K equivalent)
VALID_SIZES = {"1K", "2K", "4K"}

# Backwards compatibility
MODEL_NAME = MODEL_PRO


def load_default_system_prompt() -> Optional[str]:
    """Load the packaged default system prompt.

    Looks for thumbkit/system_prompt.md packaged with the wheel.
    Falls back to a project-root system_prompt.md when running from source.
    """
    # Try packaged resource first
    try:
        pkg_file = resources.files("thumbkit").joinpath("system_prompt.md")
        if pkg_file.is_file():
            text = pkg_file.read_text(encoding="utf-8").strip()
            if text:
                return text
    except Exception:
        pass

    return None


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable.")
    # Enable built-in retry with SDK defaults (5 attempts, exponential backoff)
    # Retries on: 408, 429, 500, 502, 503, 504
    return genai.Client(
        api_key=api_key,
        http_options=gtypes.HttpOptions(
            retry_options=gtypes.HttpRetryOptions()
        )
    )


def guess_mime(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/png"


def _inline_part_from_file(path: str) -> gtypes.Part:
    data = Path(path).read_bytes()
    return gtypes.Part(inline_data=gtypes.Blob(mime_type=guess_mime(path), data=data))


def resolve_model_name(model: str) -> str:
    """Resolve model shorthand (flash/pro) to full API model name."""
    if model in MODEL_NAMES:
        return MODEL_NAMES[model]
    # Allow passing full model name directly
    if model in MODEL_NAMES.values():
        return model
    raise ValueError(f"Unknown model: {model}. Use 'flash' or 'pro'.")


def _get_safety_settings() -> List[gtypes.SafetySetting]:
    """Return permissive safety settings to allow more creative content."""
    # Set all harm categories to OFF to minimize content filtering
    categories = [
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
        "HARM_CATEGORY_CIVIC_INTEGRITY",
    ]
    return [
        gtypes.SafetySetting(category=cat, threshold="OFF")
        for cat in categories
    ]


def generate_image_bytes(
    prompt: str,
    reference_image_paths: Optional[List[str]] = None,
    *,
    system_prompt: Optional[str] = None,
    aspect_ratio: str = "16:9",
    model: str = DEFAULT_MODEL,
    image_size: Optional[str] = DEFAULT_SIZE,
) -> Tuple[bytes, dict]:
    """Generate an image and return (image_bytes, metadata).

    Args:
        prompt: Text description of the desired image.
        reference_image_paths: Optional list of reference image paths.
        system_prompt: Optional system prompt override.
        aspect_ratio: Output aspect ratio (default: 16:9).
        model: Model to use - 'pro' (default) or 'flash'.
        image_size: Output size for Pro model - '1K', '2K', or '4K'. Ignored for Flash.

    Returns:
        Tuple of (image_bytes, metadata_dict).
    """
    client = _get_client()
    model_name = resolve_model_name(model)

    parts: list = []
    if reference_image_paths:
        for p in reference_image_paths:
            parts.append(_inline_part_from_file(p))
    parts.append(prompt)

    # Build image config - size only applies to Pro model
    # SDK uses camelCase: aspectRatio, imageSize
    image_config_kwargs = {"aspectRatio": aspect_ratio}
    if model_name == MODEL_PRO and image_size and image_size in VALID_SIZES:
        image_config_kwargs["imageSize"] = image_size

    cfg = gtypes.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=gtypes.ImageConfig(**image_config_kwargs),
        safety_settings=_get_safety_settings(),
    )
    if system_prompt:
        cfg.system_instruction = gtypes.Content(parts=[gtypes.Part(text=system_prompt)])

    response = client.models.generate_content(model=model_name, contents=parts, config=cfg)

    # Better error handling for empty/filtered responses
    if not response.candidates:
        block_reason = getattr(response, 'prompt_feedback', None)
        raise RuntimeError(f"Gemini returned no candidates. Prompt feedback: {block_reason}")

    candidate = response.candidates[0]
    if not candidate.content or not candidate.content.parts:
        finish_reason = getattr(candidate, 'finish_reason', 'unknown')
        safety_ratings = getattr(candidate, 'safety_ratings', None)
        raise RuntimeError(
            f"Gemini returned empty content. Finish reason: {finish_reason}, "
            f"Safety ratings: {safety_ratings}"
        )

    image_bytes: Optional[bytes] = None
    for part in candidate.content.parts:
        if getattr(part, "inline_data", None):
            image_bytes = part.inline_data.data
            break
    if image_bytes is None:
        raise RuntimeError("Gemini did not return image data in response parts.")

    meta = {
        "model": model,
        "model_name": model_name,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size if model_name == MODEL_PRO else None,
        "reference_image_paths": reference_image_paths or [],
    }
    return image_bytes, meta


def edit_image_bytes(
    prompt: str,
    base_image_path: str,
    reference_image_paths: Optional[List[str]] = None,
    *,
    system_prompt: Optional[str] = None,
    aspect_ratio: str = "16:9",
    model: str = DEFAULT_MODEL,
    image_size: Optional[str] = DEFAULT_SIZE,
) -> Tuple[bytes, dict]:
    """Edit an image and return (image_bytes, metadata).

    Args:
        prompt: Edit instructions in natural language.
        base_image_path: Path to the primary image to edit.
        reference_image_paths: Optional list of additional reference image paths.
        system_prompt: Optional system prompt override.
        aspect_ratio: Output aspect ratio (default: 16:9).
        model: Model to use - 'pro' (default) or 'flash'.
        image_size: Output size for Pro model - '1K', '2K', or '4K'. Ignored for Flash.

    Returns:
        Tuple of (image_bytes, metadata_dict).
    """
    client = _get_client()
    model_name = resolve_model_name(model)

    parts: list = []
    # Base first
    parts.append(_inline_part_from_file(base_image_path))
    # Optional references
    if reference_image_paths:
        for p in reference_image_paths:
            parts.append(_inline_part_from_file(p))
    # Text last
    parts.append(prompt)

    # Build image config - size only applies to Pro model
    # SDK uses camelCase: aspectRatio, imageSize
    image_config_kwargs = {"aspectRatio": aspect_ratio}
    if model_name == MODEL_PRO and image_size and image_size in VALID_SIZES:
        image_config_kwargs["imageSize"] = image_size

    cfg = gtypes.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=gtypes.ImageConfig(**image_config_kwargs),
        safety_settings=_get_safety_settings(),
    )
    if system_prompt:
        cfg.system_instruction = gtypes.Content(parts=[gtypes.Part(text=system_prompt)])

    response = client.models.generate_content(model=model_name, contents=parts, config=cfg)

    # Better error handling for empty/filtered responses
    if not response.candidates:
        block_reason = getattr(response, 'prompt_feedback', None)
        raise RuntimeError(f"Gemini returned no candidates. Prompt feedback: {block_reason}")

    candidate = response.candidates[0]
    if not candidate.content or not candidate.content.parts:
        finish_reason = getattr(candidate, 'finish_reason', 'unknown')
        safety_ratings = getattr(candidate, 'safety_ratings', None)
        raise RuntimeError(
            f"Gemini returned empty content. Finish reason: {finish_reason}, "
            f"Safety ratings: {safety_ratings}"
        )

    image_bytes: Optional[bytes] = None
    for part in candidate.content.parts:
        if getattr(part, "inline_data", None):
            image_bytes = part.inline_data.data
            break
    if image_bytes is None:
        raise RuntimeError("Gemini did not return image data in response parts.")

    meta = {
        "model": model,
        "model_name": model_name,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size if model_name == MODEL_PRO else None,
        "base_image_path": base_image_path,
        "reference_image_paths": reference_image_paths or [],
    }
    return image_bytes, meta


def save_image_bytes(image_bytes: bytes, out_dir: Path, *, prefix: str = "thumbkit") -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")
    path = out_dir / f"{prefix}-{ts}.png"
    path.write_bytes(image_bytes)
    return str(path)
