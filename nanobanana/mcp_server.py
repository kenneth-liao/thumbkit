import os
from pathlib import Path
from typing import List, Optional

from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from fastmcp.tools.tool import ToolResult

from nanobanana.core import (
    MODEL_NAME,
    generate_image_bytes,
    edit_image_bytes,
    load_default_system_prompt,
    save_image_bytes,
)
from dotenv import load_dotenv
load_dotenv()


# Server name displayed to MCP clients
mcp = FastMCP("nanobanana")

# Output dir: $NANOBANANA_OUTPUT_DIR or a hidden folder in CWD
env = os.environ.get("NANOBANANA_OUTPUT_DIR")
OUTPUT_DIR = (Path(env) if env else (Path.cwd() / ".nanobanana-generations")).resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
    system_prompt = load_default_system_prompt()
    image_bytes, meta = generate_image_bytes(
        prompt=prompt,
        reference_image_paths=reference_image_paths,
        system_prompt=system_prompt,
        aspect_ratio="16:9",
        model_name=MODEL_NAME,
    )

    file_path = save_image_bytes(image_bytes, OUTPUT_DIR, prefix="nanobanana")
    content = [Image(data=image_bytes, format="png"), f"Saved to {file_path}"]
    structured = {"file_path": file_path, "bytes": len(image_bytes), **meta}
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
    system_prompt = load_default_system_prompt()
    image_bytes, meta = edit_image_bytes(
        prompt=prompt,
        base_image_path=base_image_path,
        reference_image_paths=reference_image_paths,
        system_prompt=system_prompt,
        aspect_ratio="16:9",
        model_name=MODEL_NAME,
    )

    file_path = save_image_bytes(image_bytes, OUTPUT_DIR, prefix="nanobanana-edit")
    content = [Image(data=image_bytes, format="png"), f"Saved to {file_path}"]
    structured = {"file_path": file_path, "bytes": len(image_bytes), **meta}
    return ToolResult(content=content, structured_content=structured)


def main() -> None:
    # Direct execution entrypoint for FastMCP
    mcp.run()


if __name__ == "__main__":
    main()

