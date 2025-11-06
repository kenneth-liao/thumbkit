import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from importlib import resources
from google import genai
from google.genai import types as gtypes

MODEL_NAME = "gemini-2.5-flash-image"


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
    return genai.Client(api_key=api_key)


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


def generate_image_bytes(
    prompt: str,
    reference_image_paths: Optional[List[str]] = None,
    *,
    system_prompt: Optional[str] = None,
    aspect_ratio: str = "16:9",
    model_name: str = MODEL_NAME,
) -> Tuple[bytes, dict]:
    """Generate an image and return (image_bytes, metadata)."""
    client = _get_client()

    parts: list = []
    if reference_image_paths:
        for p in reference_image_paths:
            parts.append(_inline_part_from_file(p))
    parts.append(prompt)

    cfg = gtypes.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=gtypes.ImageConfig(aspect_ratio=aspect_ratio),
    )
    if system_prompt:
        cfg.system_instruction = gtypes.Content(parts=[gtypes.Part(text=system_prompt)])

    response = client.models.generate_content(model=model_name, contents=parts, config=cfg)

    image_bytes: Optional[bytes] = None
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            image_bytes = part.inline_data.data
            break
    if image_bytes is None:
        raise RuntimeError("Gemini did not return image data.")

    meta = {
        "aspect_ratio": aspect_ratio,
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
    model_name: str = MODEL_NAME,
) -> Tuple[bytes, dict]:
    """Edit an image and return (image_bytes, metadata)."""
    client = _get_client()

    parts: list = []
    # Base first
    parts.append(_inline_part_from_file(base_image_path))
    # Optional references
    if reference_image_paths:
        for p in reference_image_paths:
            parts.append(_inline_part_from_file(p))
    # Text last
    parts.append(prompt)

    cfg = gtypes.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=gtypes.ImageConfig(aspect_ratio=aspect_ratio),
    )
    if system_prompt:
        cfg.system_instruction = gtypes.Content(parts=[gtypes.Part(text=system_prompt)])

    response = client.models.generate_content(model=model_name, contents=parts, config=cfg)

    image_bytes: Optional[bytes] = None
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            image_bytes = part.inline_data.data
            break
    if image_bytes is None:
        raise RuntimeError("Gemini did not return image data.")

    meta = {
        "aspect_ratio": aspect_ratio,
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

