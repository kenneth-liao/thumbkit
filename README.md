# thumbkit

A YouTube thumbnail generator that drives the Gemini “Nano Banana” image generation model via the Gemini API.

Provides both:
- **CLI tool** (`thumbkit`) - Command-line interface for generating and editing thumbnails
- **MCP server** (`thumbkit-mcp`) - Model Context Protocol server for Claude Desktop integration

## MCP Requirements

- All returned images are 16:9 aspect ratio (optimized for YouTube thumbnails).
- Ability to edit images by passing a prompt, a base/original image to edit, and optional reference images for style transfer.

## Gemini Image Generation

Official docs: https://ai.google.dev/gemini-api/docs/image-generation

This server targets the `gemini-2.5-flash-image` model and configures:
- `response_modalities=['Image']` so the model returns images
- `image_config.aspect_ratio='16:9'` to enforce 16:9 outputs

## Tools exposed

- `generate_image(prompt: str)` → generates a 16:9 image from text
- `edit_image(prompt: str, base_image_path: str, reference_image_paths: Optional[List[str]])` → edits a base image and optionally uses reference images for style transfer; returns a 16:9 image

Each tool returns:
- An inline image content block (MCP ImageContent), and
- Structured metadata including a file path where the image is saved under `./outputs/`

## Quick Start - CLI Tool

Install globally:

```bash
uv tool install git+https://github.com/kenneth-liao/thumbkit.git
```

View full documentation:

```bash
thumbkit docs
```

Generate a thumbnail:

```bash
export GEMINI_API_KEY=your_api_key_here
thumbkit generate --prompt "Create an eye-catching YouTube thumbnail"
```

**For Claude Agents:** Run `thumbkit docs` to get the complete, version-matched CLI reference. This ensures you always have documentation that matches the installed version.

## Setup for Development

1) Ensure Python 3.13+ and `uv` are installed.
2) Set your Gemini API key in the environment (the SDK accepts `GEMINI_API_KEY` or `GOOGLE_API_KEY`):

```bash
export GEMINI_API_KEY=your_api_key_here
```

3) Install dependencies.

This project already includes `fastmcp` and `google-genai` in pyproject.

> Note: Per repo policy we use package managers and avoid hand-editing pyproject. Please run:

```bash
uv sync
```

Optional (for the MCP Inspector CLI):

```bash
uv add mcp
```

## Run (local dev with MCP Inspector)

```bash
uv run mcp dev thumbkit/mcp_server.py
```

This launches a local MCP Inspector for testing. You should see the `thumbkit` server with two tools.

## Install into Claude Desktop (optional)

```bash
uvx thumbkit-mcp
```

Or install via `mcp` CLI:

```bash
uv run mcp install thumbkit/mcp_server.py --name thumbkit
```

You can pass env vars at install time as needed:

```bash
uv run mcp install thumbkit/mcp_server.py --name thumbkit -v GEMINI_API_KEY=$GEMINI_API_KEY
```

## Examples

- Generate an image:

```bash
# From the Inspector or any MCP client, call:
# Tool: generate_image
# Args: {"prompt": "Create a cinematic close-up of a nano banana on a futuristic table"}
```

- Edit an image with references:

```bash
# Tool: edit_image
# Args example:
# {
#   "prompt": "Make the base image in the style of the reference, with neon highlights",
#   "base_image_path": "./examples/base.png",
#   "reference_image_paths": ["./examples/style1.png", "./examples/style2.jpg"]
# }
```

Outputs are saved under `./outputs/` and also returned inline to clients that support MCP ImageContent.
