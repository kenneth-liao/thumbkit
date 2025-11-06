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
7. [Error Handling](#error-handling)
8. [Best Practices for Claude Agents](#best-practices-for-claude-agents)

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

## Installation

### Global Installation (Recommended)

Install thumbkit globally so it's available from anywhere on your system:

```bash
# Install from GitHub
uv tool install git+https://github.com/kenneth-liao/thumbkit.git

# Run from anywhere
thumbkit <command> [options]
```

### Update Existing Installation

```bash
# Upgrade to latest version
uv tool upgrade thumbkit
```

### Development Installation

For local development only:

```bash
# Clone the repository
git clone https://github.com/kenneth-liao/thumbkit.git
cd thumbkit

# Install dependencies
uv sync

# Run commands (local development only)
uv run thumbkit <command> [options]
```

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

## Commands

### `generate` Command

Generate a new thumbnail from a text prompt with optional reference images.

#### Syntax

```bash
thumbkit generate --prompt "PROMPT" [OPTIONS]
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

**⚠️ IMPORTANT: Use ABSOLUTE paths for reference images!**

Since `thumbkit` is installed globally and can be run from any directory, you **MUST** provide absolute paths to reference images. Relative paths will fail because they're resolved from your current working directory, not where the images actually are.

**✅ CORRECT - Absolute paths:**
```bash
thumbkit generate \
  --prompt "Tech tutorial thumbnail with neon highlights" \
  --ref /Users/username/images/style1.png \
  --ref /Users/username/images/style2.jpg
```

**❌ WRONG - Relative paths (will fail if run from different directory):**
```bash
thumbkit generate \
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

### `edit` Command

Edit an existing image with optional reference images for style transfer.

#### Syntax

```bash
thumbkit edit --prompt "EDIT_INSTRUCTIONS" --base "BASE_IMAGE" [OPTIONS]
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

#### Image Paths

**⚠️ CRITICAL: ALL image paths (--base and --ref) MUST be ABSOLUTE paths!**

Since `thumbkit` runs globally from any directory, relative paths will fail. Always use absolute paths.

**✅ CORRECT:**
```bash
thumbkit edit \
  --prompt "Make it more dramatic" \
  --base /Users/username/thumbnails/original.png \
  --ref /Users/username/styles/cinematic.jpg
```

**❌ WRONG:**
```bash
thumbkit edit \
  --prompt "Make it more dramatic" \
  --base ./original.png \
  --ref ../styles/cinematic.jpg
```

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
thumbkit generate \
  --prompt "Gaming thumbnail" \
  --system-prompt custom_instructions.txt
```

The custom prompt file should be plain text (UTF-8 encoded).

## Error Handling

thumbkit provides **comprehensive, actionable error messages** specifically designed to help Claude agents debug and fix issues quickly. Every error includes:
- Clear description of what went wrong
- Specific solution steps
- Code examples when applicable

### Common Errors and Solutions

#### 1. Invalid File Type

**Error:**
```
ERROR: --ref (image #1) has unsupported file extension: .gif

SOLUTION: Use one of these supported image formats:
  - PNG (.png)
  - JPEG (.jpg, .jpeg)
  - WebP (.webp)

Current file: /Users/username/image.gif
```

**What to do:** Convert the image to PNG, JPEG, or WebP format.

#### 2. No Image Returned from API

**Error:**
```
ERROR: Gemini API did not return image data.

POSSIBLE CAUSES:
  1. The prompt may have triggered content safety filters
  2. The API request may have failed
  3. The reference images may be incompatible

SOLUTIONS:
  - Try rephrasing your prompt to be less specific about people/brands
  - Verify your API key is valid and has quota remaining
  - Try without reference images to isolate the issue
  - Check if reference images are valid and not corrupted
```

**What to do:** Follow the troubleshooting steps in order.

#### 3. Multiple Reference Images Syntax Error

**Error:**
```
thumbkit generate: error: the following arguments are required: --prompt

HINT: Common mistakes:
  - To pass multiple reference images, use --ref multiple times:
    thumbkit generate --prompt "..." --ref /path/1.png --ref /path/2.png
  - All image paths MUST be absolute paths (start with /)
  - Use --help to see all available options
```

**What to do:** Use `--ref` flag multiple times, not as a list.

**❌ WRONG:**
```bash
thumbkit generate --prompt "test" --ref ["/path/1.png", "/path/2.png"]
```

**✅ CORRECT:**
```bash
thumbkit generate --prompt "test" --ref /path/1.png --ref /path/2.png
```

### Exit Codes

- `0` - Success
- `1` - Error occurred (detailed message in stderr)

## Best Practices for Claude Agents

### ⚠️ CRITICAL: Always Use Absolute Paths for Images

**This is the #1 most important rule when using thumbkit!**

- **ALWAYS** use absolute paths for `--ref` and `--base` arguments
- **NEVER** use relative paths (e.g., `./image.png`, `../folder/image.jpg`)
- Since thumbkit runs globally, relative paths will fail when run from different directories

### Handling Reference Images

**⚠️ REMEMBER: All image paths MUST be absolute!**

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

**Common fixes:**
- **Path errors** → Convert to absolute paths using `os.path.abspath()`
- **File not found** → Verify file exists and path is correct
- **API errors** → Check API key, quota, and network connection
- **Syntax errors** → Use `--ref` multiple times, not as a list

**If error persists after following solutions:**
1. Verify you're using the latest version: `uv tool upgrade thumbkit`
2. Check the error type - some errors (like content filters) may require prompt changes
3. Try a simpler version of the command to isolate the issue

### Performance Considerations

- Generation typically takes 5-15 seconds
- Larger reference images may take longer to process
- Multiple reference images increase processing time
- Use `--json` for faster parsing (no need to parse human-readable text)

## Additional Notes

- The CLI automatically loads `.env` files in the current directory
- All timestamps are in UTC
- Images are always returned as PNG regardless of reference image formats
- The system prompt is embedded in the package and loaded automatically
- Custom system prompts must be UTF-8 encoded text files
