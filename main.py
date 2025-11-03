import asyncio
import base64
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from google import genai
from google.genai import types as gtypes

# FastMCP is the simplest way to stand up an MCP server in Python
from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from fastmcp.tools.tool import ToolResult

from dotenv import load_dotenv
load_dotenv()

# Server name displayed to MCP clients
mcp = FastMCP("nanobanana")

OUTPUT_DIR = Path("/Users/kennethliao/Movies/YT/thumbnails/gemini-generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "gemini-2.5-flash-image"  # "Nano Banana" image model alias per docs
# Load a default system prompt (if present) from system_prompt.md at project root
_PROJECT_ROOT = Path(__file__).resolve().parent
_SYSTEM_PROMPT_PATH = _PROJECT_ROOT / "system_prompt.md"


def _load_system_prompt() -> Optional[str]:
    try:
        if _SYSTEM_PROMPT_PATH.exists():
            text = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
            return text if text else None
    except Exception:
        # Be silent if there's any read/encoding error; treat as absent
        pass
    return None


SYSTEM_PROMPT: Optional[str] = _load_system_prompt()



def _get_client() -> genai.Client:
    """Create a Google GenAI client. Requires GEMINI_API_KEY env var to be set.
    The google-genai SDK will also read GOOGLE_API_KEY if set.
    """
    # Let the SDK pick up API key from env; raise a clearer message if missing
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # Do not print; raise to return a clear error via MCP
        raise RuntimeError(
            "Missing GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable."
        )
    return genai.Client(api_key=api_key)


def _save_image_bytes(image_bytes: bytes, prefix: str = "image") -> str:
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")
    path = OUTPUT_DIR / f"{prefix}-{ts}.png"
    with open(path, "wb") as f:
        f.write(image_bytes)
    return str(path)


@mcp.tool()
def generate_image(prompt: str, reference_image_paths: Optional[List[str]] = None) -> ToolResult:
    """Generate a 16:9 image from a text prompt using Gemini's image model.

    Args:
      prompt: Text description of the desired image.
      reference_image_paths: Optional list of file paths to images used as
        style/composition references. When provided, these images are sent
        before the text prompt so the model can use them to guide style,
        palette, subject emphasis, or layout. Use this for guided generation
        (not necessarily preserving a specific base image). 1–3 references
        typically work best. PNG/JPEG/WebP are supported.

    Returns:
      A ToolResult with an image content block and structured metadata.
    """
    client = _get_client()
    # Optional reference images to guide style/composition
    parts: list = []
    if reference_image_paths:
        for p in reference_image_paths:
            with open(p, "rb") as f:
                ref_bytes = f.read()
            parts.append(
                gtypes.Part(
                    inline_data=gtypes.Blob(mime_type=_guess_mime(p), data=ref_bytes)
                )
            )
    # Add the textual prompt last
    parts.append(prompt)


    cfg = gtypes.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=gtypes.ImageConfig(aspect_ratio="16:9"),
    )
    if SYSTEM_PROMPT:
        cfg.system_instruction = gtypes.Content(parts=[gtypes.Part(text=SYSTEM_PROMPT)])
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=parts,
        config=cfg,
    )

    # Find first image part in the response
    image_bytes: Optional[bytes] = None
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            image_bytes = part.inline_data.data
            break
    if image_bytes is None:
        raise RuntimeError("Gemini did not return image data.")

    file_path = _save_image_bytes(image_bytes, prefix="nanobanana")

    # Return both an Image (auto-converted to ImageContent) and structured metadata
    content = [
        Image(data=image_bytes, format="png"),
        f"Saved to {file_path}",
    ]
    structured = {"file_path": file_path, "bytes": len(image_bytes), "aspect_ratio": "16:9", "reference_image_paths": reference_image_paths or []}
    return ToolResult(content=content, structured_content=structured)


@mcp.tool()
def edit_image(
    prompt: str,
    base_image_path: str,
    reference_image_paths: Optional[List[str]] = None,
) -> ToolResult:
    """Edit an image by providing a prompt and one or more input images.

    Use this when you want to preserve and modify a specific base image. The
    model treats the base image as the subject/layout to transform. For guided
    generation without preserving a particular base, prefer
    `generate_image(prompt, reference_image_paths=...)`.

    Args:
      prompt: Edit instructions in natural language.
      base_image_path: Path to the primary image to edit (the model will
        preserve/transform this image as the basis of the result).
      reference_image_paths: Optional list of additional image paths (1–3
        recommended) to steer style, palette, lighting, or composition. These
        are used as guidance; the base image remains the primary subject. PNG/
        JPEG/WebP are supported. The order of references can influence style
        emphasis.

    Returns:
      A ToolResult with an image content block and structured metadata.
    """
    client = _get_client()

    # Read image bytes and construct inline data parts
    parts: list = []

    def _read_image(path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    # Base image first
    base_bytes = _read_image(base_image_path)
    parts.append(
        gtypes.Part(
            inline_data=gtypes.Blob(mime_type=_guess_mime(base_image_path), data=base_bytes)
        )
    )

    # Optional reference images
    if reference_image_paths:
        for p in reference_image_paths:
            ref_bytes = _read_image(p)
            parts.append(
                gtypes.Part(
                    inline_data=gtypes.Blob(mime_type=_guess_mime(p), data=ref_bytes)
                )
            )

    # Add the textual instruction last
    parts.append(prompt)

    cfg = gtypes.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=gtypes.ImageConfig(aspect_ratio="16:9"),
    )
    if SYSTEM_PROMPT:
        cfg.system_instruction = gtypes.Content(parts=[gtypes.Part(text=SYSTEM_PROMPT)])
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=parts,
        config=cfg,
    )

    image_bytes: Optional[bytes] = None
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            image_bytes = part.inline_data.data
            break
    if image_bytes is None:
        raise RuntimeError("Gemini did not return image data.")

    file_path = _save_image_bytes(image_bytes, prefix="nanobanana-edit")

    content = [
        Image(data=image_bytes, format="png"),
        f"Saved to {file_path}",
    ]
    structured = {
        "file_path": file_path,
        "bytes": len(image_bytes),
        "aspect_ratio": "16:9",
        "base_image_path": base_image_path,
        "reference_image_paths": reference_image_paths or [],
    }
    return ToolResult(content=content, structured_content=structured)


def _guess_mime(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    # Default to PNG
    return "image/png"


def main() -> None:
    # Direct execution entrypoint for FastMCP
    # Do NOT print to stdout; MCP uses stdio for protocol messages.
    mcp.run()


if __name__ == "__main__":
    main()
