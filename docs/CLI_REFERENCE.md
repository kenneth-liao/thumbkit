# thumbkit CLI Reference

**Version:** 0.1.0  
**Model:** Gemini 2.5 Flash Image (`gemini-2.5-flash-image`)  
**Purpose:** Generate and edit YouTube thumbnails using AI

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Environment Setup](#environment-setup)
4. [Commands](#commands)
   - [generate](#generate-command)
   - [edit](#edit-command)
5. [Output Behavior](#output-behavior)
6. [System Prompt](#system-prompt)
7. [Examples](#examples)
8. [Error Handling](#error-handling)
9. [Best Practices for Claude Agents](#best-practices-for-claude-agents)

---

## Overview

`thumbkit` is a CLI tool for generating YouTube thumbnails using Google's Gemini image generation model. It provides two main commands:

- **`generate`** - Create new thumbnails from text prompts with optional reference images
- **`edit`** - Modify existing images with optional reference images for style transfer

All generated images are:
- **16:9 aspect ratio** by default (YouTube thumbnail standard)
- **PNG format**
- Saved with timestamped filenames
- Optimized for high-converting YouTube thumbnails

---

## Installation

```bash
# Install via uv (recommended)
uv sync

# Run commands
uv run thumbkit <command> [options]

# Or install globally
uvx thumbkit <command> [options]
```

---

## Environment Setup

### Required Environment Variables

**`GEMINI_API_KEY`** or **`GOOGLE_API_KEY`** (required)
- Your Gemini API key for authentication
- Get one at: https://ai.google.dev/

```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Optional Environment Variables

**`THUMBKIT_OUTPUT_DIR`** (optional)
- Custom output directory for generated images
- If not set, defaults to `.thumbkit-generations/` in current working directory

```bash
export THUMBKIT_OUTPUT_DIR="/path/to/output"
```

---

## Commands

### `generate` Command

Generate a new thumbnail from a text prompt with optional reference images.

#### Syntax

```bash
uv run thumbkit generate --prompt "PROMPT" [OPTIONS]
```

#### Required Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--prompt` | string | Text description of the thumbnail to generate (required) |

#### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--ref` | path | None | Reference image file path (repeatable for multiple images) |
| `--aspect` | string | `16:9` | Aspect ratio for output image |
| `--system-prompt` | path | Built-in | Path to custom system prompt file (overrides default) |
| `--out-dir` | path | `.thumbkit-generations/` | Output directory for generated image |
| `--json` | flag | false | Output result as JSON instead of human-readable text |

#### Reference Images

Reference images are used for **style transfer** and **visual guidance**:
- Provide visual examples of desired style, composition, or aesthetic
- Can specify multiple reference images using `--ref` multiple times
- Supported formats: PNG, JPEG, WebP
- Images are sent to Gemini before the text prompt

**Example:**
```bash
uv run thumbkit generate \
  --prompt "Tech tutorial thumbnail with neon highlights" \
  --ref examples/style1.png \
  --ref examples/style2.jpg
```

#### Output

**Without `--json` flag:**
```
Saved to /path/to/.thumbkit-generations/thumbkit-20251106-214644-047173.png
```

**With `--json` flag:**
```json
{
  "file_path": "/path/to/.thumbkit-generations/thumbkit-20251106-214644-047173.png",
  "bytes": 1265727,
  "aspect_ratio": "16:9",
  "reference_image_paths": []
}
```

---

### `edit` Command

Edit an existing image with optional reference images for style transfer.

#### Syntax

```bash
uv run thumbkit edit --prompt "EDIT_INSTRUCTIONS" --base "BASE_IMAGE" [OPTIONS]
```

#### Required Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--prompt` | string | Edit instructions describing desired changes (required) |
| `--base` | path | Path to base image to edit (required) |

#### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--ref` | path | None | Reference image file path for style transfer (repeatable) |
| `--aspect` | string | `16:9` | Aspect ratio for output image |
| `--system-prompt` | path | Built-in | Path to custom system prompt file (overrides default) |
| `--out-dir` | path | `.thumbkit-generations/` | Output directory for edited image |
| `--json` | flag | false | Output result as JSON instead of human-readable text |

#### Image Order

When using `edit`, images are sent to Gemini in this order:
1. **Base image** (the image to edit)
2. **Reference images** (optional style guides)
3. **Text prompt** (edit instructions)

#### Output

**Without `--json` flag:**
```
Saved to /path/to/.thumbkit-generations/thumbkit-edit-20251106-214644-047173.png
```

**With `--json` flag:**
```json
{
  "file_path": "/path/to/.thumbkit-generations/thumbkit-edit-20251106-214644-047173.png",
  "bytes": 1456892,
  "aspect_ratio": "16:9",
  "base_image_path": "original.png",
  "reference_image_paths": ["style.png"]
}
```

---

## Output Behavior

### File Naming Convention

Generated files use timestamped names:

- **Generate command:** `thumbkit-YYYYMMDD-HHMMSS-microseconds.png`
- **Edit command:** `thumbkit-edit-YYYYMMDD-HHMMSS-microseconds.png`

**Example:** `thumbkit-20251106-214644-047173.png`

### Output Directory Priority

1. `--out-dir` argument (if provided)
2. `$THUMBKIT_OUTPUT_DIR` environment variable (if set)
3. `.thumbkit-generations/` in current working directory (default)

### File Format

- All images are saved as **PNG** format
- Images are always **16:9 aspect ratio** (unless `--aspect` is changed)
- File paths are returned as absolute paths

---

## System Prompt

thumbkit includes a comprehensive built-in system prompt that guides the AI to create high-converting YouTube thumbnails. The system prompt emphasizes:

### Critical Requirements

1. **Pass The Glance Test** - Viewer must understand in ≤1 second
2. **Spark Curiosity** - #1 most important principle for clicks
3. **Single Clear Focal Point** - One dominant element, not multiple
4. **Mobile-First Design** - Must work at small sizes

### Text Guidelines

- ✅ Complement (don't repeat) the video title
- ✅ Keep text minimal and impactful
- ✅ Ensure readability at mobile size
- ❌ Never repeat the video title
- ❌ Avoid too much text

### Visual Composition

- ✅ Bold, vibrant colors with high contrast
- ✅ Feature people (especially faces)
- ✅ Simple, uncluttered compositions
- ❌ Avoid multiple competing elements

### Custom System Prompt

Override the default with `--system-prompt`:

```bash
uv run thumbkit generate \
  --prompt "Gaming thumbnail" \
  --system-prompt custom_instructions.txt
```

The custom prompt file should be plain text (UTF-8 encoded).

---

## Examples

### Basic Generation

```bash
uv run thumbkit generate --prompt "Coding tutorial with Python logo"
```

### Generation with Reference Images

```bash
uv run thumbkit generate \
  --prompt "Tech review thumbnail with neon aesthetic" \
  --ref examples/neon-style.png \
  --ref examples/tech-layout.jpg
```

### Generation with JSON Output

```bash
uv run thumbkit generate \
  --prompt "Fitness transformation thumbnail" \
  --json
```

### Edit Existing Image

```bash
uv run thumbkit edit \
  --prompt "Add dramatic lighting and increase contrast" \
  --base original-thumbnail.png
```

### Edit with Style Transfer

```bash
uv run thumbkit edit \
  --prompt "Apply the style from the reference images" \
  --base my-thumbnail.png \
  --ref cinematic-style.png \
  --ref color-grading.jpg
```

### Custom Output Directory

```bash
uv run thumbkit generate \
  --prompt "Travel vlog thumbnail" \
  --out-dir ~/Desktop/thumbnails
```

### Custom Aspect Ratio

```bash
uv run thumbkit generate \
  --prompt "Instagram post" \
  --aspect "1:1"
```

---

## Error Handling

### Common Errors

**Missing API Key:**
```
Error: Missing GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable.
```
**Solution:** Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable

**File Not Found:**
```
Error: [Errno 2] No such file or directory: 'image.png'
```
**Solution:** Verify file paths are correct and files exist

**No Image Returned:**
```
Error: Gemini did not return image data.
```
**Solution:** Check API key validity, prompt quality, or try again

### Exit Codes

- `0` - Success
- `1` - Error occurred (check stderr for details)

---

## Best Practices for Claude Agents

### When to Use `generate` vs `edit`

**Use `generate` when:**
- Creating a new thumbnail from scratch
- User provides only text description
- No existing image to modify

**Use `edit` when:**
- User has an existing image to modify
- User wants to apply style transfer
- User wants to refine/improve an existing thumbnail

### Handling Reference Images

**Reference images are for style/composition guidance, NOT content:**
- Use references to show desired visual style, color palette, or layout
- Don't expect the model to copy specific elements from references
- Multiple references can provide richer style guidance

### Prompt Engineering Tips

**Good prompts are:**
- Specific about visual elements (colors, composition, subjects)
- Clear about the video topic/theme
- Descriptive of desired mood/emotion
- Concise but detailed

**Example good prompts:**
- ✅ "Dramatic close-up of a shocked face with bold yellow text 'UNBELIEVABLE' on vibrant red background"
- ✅ "Split-screen comparison showing before/after transformation with arrow pointing right"
- ❌ "Make a thumbnail" (too vague)
- ❌ "Create something cool" (not specific)

### Using JSON Output

**Always use `--json` flag when:**
- You need to parse the output programmatically
- You need the file path for further processing
- You're chaining multiple commands together

**Parse the JSON to extract:**
- `file_path` - Absolute path to generated image
- `bytes` - File size in bytes
- `aspect_ratio` - Confirmed aspect ratio
- `reference_image_paths` - List of reference images used

### Error Recovery

**If generation fails:**
1. Check API key is valid and set
2. Verify all file paths exist
3. Simplify the prompt if it's complex
4. Try again (API may have temporary issues)
5. Check stderr for specific error messages

### Performance Considerations

- Generation typically takes 5-15 seconds
- Larger reference images may take longer to process
- Multiple reference images increase processing time
- Use `--json` for faster parsing (no need to parse human-readable text)

---

## Additional Notes

- The CLI automatically loads `.env` files in the current directory
- All timestamps are in UTC
- Images are always returned as PNG regardless of reference image formats
- The system prompt is embedded in the package and loaded automatically
- Custom system prompts must be UTF-8 encoded text files

