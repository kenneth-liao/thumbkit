import argparse
import json
import os
import sys
from importlib import metadata
from pathlib import Path
from typing import List, Optional

from importlib import resources
from dotenv import load_dotenv, find_dotenv
from thumbkit.core import (
    DEFAULT_MODEL,
    DEFAULT_SIZE,
    VALID_SIZES,
    generate_image_bytes,
    edit_image_bytes,
    load_default_system_prompt,
    save_image_bytes,
)

def get_version() -> str:
    """Get the package version from metadata."""
    try:
        return metadata.version("thumbkit")
    except metadata.PackageNotFoundError:
        return "0.0.0-dev"
    

# Cross-platform path to ~/.claude/.env
claude_env_path = os.path.join(os.path.expanduser("~"), ".claude", ".env")
if os.path.exists(claude_env_path):
    load_dotenv(claude_env_path, override=True)

# Load .env from current working directory or parent directories
load_dotenv(find_dotenv(usecwd=True))


class ThumbkitError(Exception):
    """Base exception for thumbkit CLI errors with helpful messages for Claude agents."""
    pass


def validate_image_path(path: str, arg_name: str) -> None:
    """Validate that an image path exists and is accessible.

    Raises ThumbkitError with helpful message if validation fails.
    """
    p = Path(path)

    # Check if path is absolute
    if not p.is_absolute():
        raise ThumbkitError(
            f"ERROR: {arg_name} must be an ABSOLUTE path, but got relative path: {path}\n\n"
            f"SOLUTION: Convert to absolute path before calling thumbkit.\n"
            f"Examples:\n"
            f"  Python: os.path.abspath('{path}')\n"
            f"  Shell:  $(realpath {path})\n\n"
            f"Since thumbkit is installed globally, it can be run from any directory.\n"
            f"Relative paths will fail because they're resolved from the current working directory.\n"
            f"Always use absolute paths like: /Users/username/images/file.png"
        )

    # Check if file exists
    if not p.exists():
        raise ThumbkitError(
            f"ERROR: {arg_name} file does not exist: {path}\n\n"
            f"SOLUTION: Verify the file path is correct and the file exists.\n"
            f"Check for typos in the path or ensure the file hasn't been moved/deleted."
        )

    # Check if it's a file (not a directory)
    if not p.is_file():
        raise ThumbkitError(
            f"ERROR: {arg_name} path is a directory, not a file: {path}\n\n"
            f"SOLUTION: Provide the full path to an image file, not a directory.\n"
            f"Example: {path}/image.png"
        )

    # Check file extension
    valid_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
    if p.suffix.lower() not in valid_extensions:
        raise ThumbkitError(
            f"ERROR: {arg_name} has unsupported file extension: {p.suffix}\n\n"
            f"SOLUTION: Use one of these supported image formats:\n"
            f"  - PNG (.png)\n"
            f"  - JPEG (.jpg, .jpeg)\n"
            f"  - WebP (.webp)\n\n"
            f"Current file: {path}"
        )


def validate_reference_images(ref_paths: Optional[List[str]]) -> None:
    """Validate all reference image paths."""
    if not ref_paths:
        return

    for i, path in enumerate(ref_paths, 1):
        validate_image_path(path, f"--ref (image #{i})")


def _read_text(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    try:
        return Path(path).read_text(encoding="utf-8").strip() or None
    except Exception:
        return None


def _default_out_dir() -> Path:
    # Allow override via THUMBKIT_OUTPUT_DIR environment variable
    env = os.environ.get("THUMBKIT_OUTPUT_DIR")
    return Path(env) if env else (Path.cwd() / "youtube" / "thumbnails")


def cmd_generate(args: argparse.Namespace) -> int:
    # Validate reference images first
    validate_reference_images(args.ref)

    # Validate system prompt file if provided
    if args.system_prompt:
        validate_image_path(args.system_prompt, "--system-prompt")

    system_prompt = _read_text(args.system_prompt) or load_default_system_prompt()

    # Validate output directory
    if args.out_dir:
        out_dir = Path(args.out_dir)
        if out_dir.exists() and not out_dir.is_dir():
            raise ThumbkitError(
                f"ERROR: --out-dir path exists but is not a directory: {args.out_dir}\n\n"
                f"SOLUTION: Provide a directory path, not a file path."
            )

    image_bytes, meta = generate_image_bytes(
        prompt=args.prompt,
        reference_image_paths=args.ref or None,
        system_prompt=system_prompt,
        aspect_ratio=args.aspect,
        model=args.model,
        image_size=args.size,
    )

    out_dir = Path(args.out_dir) if args.out_dir else _default_out_dir()
    file_path = save_image_bytes(image_bytes, out_dir, prefix="thumbkit")

    result = {
        "file_path": file_path,
        "bytes": len(image_bytes),
        "model": meta.get("model", args.model),
        "image_size": meta.get("image_size"),
        "aspect_ratio": meta.get("aspect_ratio", args.aspect),
        "reference_image_paths": meta.get("reference_image_paths", args.ref or []),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Saved to {file_path}")
    return 0


def cmd_docs(args: argparse.Namespace) -> int:
    """Display the CLI documentation."""
    try:
        # Try to load packaged documentation
        pkg_file = resources.files("thumbkit").joinpath("CLI_REFERENCE.md")
        if pkg_file.is_file():
            docs = pkg_file.read_text(encoding="utf-8")
            print(docs)
            return 0
    except Exception as e:
        print(f"Error loading documentation: {e}", file=sys.stderr)
        return 1

    print("Error: Documentation not found in package.", file=sys.stderr)
    return 1


def cmd_edit(args: argparse.Namespace) -> int:
    # Validate base image
    validate_image_path(args.base, "--base")

    # Validate reference images
    validate_reference_images(args.ref)

    # Validate system prompt file if provided
    if args.system_prompt:
        validate_image_path(args.system_prompt, "--system-prompt")

    system_prompt = _read_text(args.system_prompt) or load_default_system_prompt()

    # Validate output directory
    if args.out_dir:
        out_dir = Path(args.out_dir)
        if out_dir.exists() and not out_dir.is_dir():
            raise ThumbkitError(
                f"ERROR: --out-dir path exists but is not a directory: {args.out_dir}\n\n"
                f"SOLUTION: Provide a directory path, not a file path."
            )

    image_bytes, meta = edit_image_bytes(
        prompt=args.prompt,
        base_image_path=args.base,
        reference_image_paths=args.ref or None,
        system_prompt=system_prompt,
        aspect_ratio=args.aspect,
        model=args.model,
        image_size=args.size,
    )

    out_dir = Path(args.out_dir) if args.out_dir else _default_out_dir()
    file_path = save_image_bytes(image_bytes, out_dir, prefix="thumbkit-edit")

    result = {
        "file_path": file_path,
        "bytes": len(image_bytes),
        "model": meta.get("model", args.model),
        "image_size": meta.get("image_size"),
        "aspect_ratio": meta.get("aspect_ratio", args.aspect),
        "base_image_path": args.base,
        "reference_image_paths": meta.get("reference_image_paths", args.ref or []),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Saved to {file_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        "thumbkit",
        description="YouTube thumbnail generator CLI (Gemini)",
        epilog="Run 'thumbkit docs' for full documentation"
    )
    p.add_argument(
        "-v", "--version",
        action="version",
        version=f"thumbkit {get_version()}"
    )
    sub = p.add_subparsers(dest="cmd", required=False)

    g = sub.add_parser("generate", help="Generate an image from text and optional reference images")
    g.add_argument("--prompt", required=True, help="Text prompt")
    g.add_argument("--ref", action="append", help="Reference image file path (repeatable)")
    g.add_argument("--aspect", default="16:9", help="Aspect ratio (default: 16:9)")
    g.add_argument("--model", default=DEFAULT_MODEL, choices=["flash", "pro"],
                   help="Model to use: 'pro' (Gemini 3 Pro, default) or 'flash' (Gemini 2.5 Flash)")
    g.add_argument("--size", default=DEFAULT_SIZE, choices=list(VALID_SIZES),
                   help="Output size for Pro model: 1K (default), 2K, or 4K. Ignored for Flash.")
    g.add_argument("--system-prompt", help="Path to a system prompt file to override default")
    g.add_argument("--out-dir", help="Output directory (default: ./youtube/thumbnails or $THUMBKIT_OUTPUT_DIR)")
    g.add_argument("--json", action="store_true", help="Print JSON result")
    g.set_defaults(func=cmd_generate)

    e = sub.add_parser("edit", help="Edit an existing image with optional references")
    e.add_argument("--prompt", required=True, help="Edit instructions")
    e.add_argument("--base", required=True, help="Base image path to edit")
    e.add_argument("--ref", action="append", help="Reference image file path (repeatable)")
    e.add_argument("--aspect", default="16:9", help="Aspect ratio (default: 16:9)")
    e.add_argument("--model", default=DEFAULT_MODEL, choices=["flash", "pro"],
                   help="Model to use: 'pro' (Gemini 3 Pro, default) or 'flash' (Gemini 2.5 Flash)")
    e.add_argument("--size", default=DEFAULT_SIZE, choices=list(VALID_SIZES),
                   help="Output size for Pro model: 1K (default), 2K, or 4K. Ignored for Flash.")
    e.add_argument("--system-prompt", help="Path to a system prompt file to override default")
    e.add_argument("--out-dir", help="Output directory (default: ./youtube/thumbnails or $THUMBKIT_OUTPUT_DIR)")
    e.add_argument("--json", action="store_true", help="Print JSON result")
    e.set_defaults(func=cmd_edit)

    d = sub.add_parser("docs", help="Display the full CLI documentation")
    d.set_defaults(func=cmd_docs)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse calls sys.exit on error, catch it to provide better messages
        if e.code != 0:
            print("\nHINT: Common mistakes:", file=sys.stderr)
            print("  - To pass multiple reference images, use --ref multiple times:", file=sys.stderr)
            print("    thumbkit generate --prompt \"...\" --ref /path/1.png --ref /path/2.png", file=sys.stderr)
            print("  - All image paths MUST be absolute paths (start with /)", file=sys.stderr)
            print("  - Use --help to see all available options", file=sys.stderr)
        raise

    # If no command provided, show help
    if not args.cmd:
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except ThumbkitError as e:
        # Our custom errors already have helpful messages
        print(str(e), file=sys.stderr)
        return 1
    except RuntimeError as e:
        # Handle errors from core.py
        error_msg = str(e)

        if "Missing GEMINI_API_KEY" in error_msg:
            print(
                "ERROR: Missing GEMINI_API_KEY environment variable.\n\n"
                "SOLUTION: Set your Gemini API key in one of these ways:\n"
                "  1. Create a .env file in your current directory:\n"
                "     echo 'GEMINI_API_KEY=your-key-here' > .env\n\n"
                "  2. Export as environment variable:\n"
                "     export GEMINI_API_KEY='your-key-here'\n\n"
                "  3. Use GOOGLE_API_KEY instead (alternative name):\n"
                "     export GOOGLE_API_KEY='your-key-here'\n\n"
                "Get your API key at: https://ai.google.dev/",
                file=sys.stderr
            )
            return 1

        if "Gemini did not return image data" in error_msg:
            print(
                "ERROR: Gemini API did not return image data.\n\n"
                "POSSIBLE CAUSES:\n"
                "  1. The prompt may have triggered content safety filters\n"
                "  2. The API request may have failed\n"
                "  3. The reference images may be incompatible\n\n"
                "SOLUTIONS:\n"
                "  - Try rephrasing your prompt to be less specific about people/brands\n"
                "  - Verify your API key is valid and has quota remaining\n"
                "  - Try without reference images to isolate the issue\n"
                "  - Check if reference images are valid and not corrupted",
                file=sys.stderr
            )
            return 1

        # Generic runtime error
        print(f"ERROR: {error_msg}\n\nIf this persists, check your API key and network connection.", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(
            f"ERROR: File not found: {e.filename}\n\n"
            f"SOLUTION: Verify the file path is correct.\n"
            f"Remember: All image paths must be ABSOLUTE paths (e.g., /Users/username/image.png)",
            file=sys.stderr
        )
        return 1
    except PermissionError as e:
        print(
            f"ERROR: Permission denied: {e.filename}\n\n"
            f"SOLUTION: Check file permissions or try a different output directory.",
            file=sys.stderr
        )
        return 1
    except Exception as e:
        # Catch-all for unexpected errors
        print(
            f"ERROR: Unexpected error occurred: {type(e).__name__}: {e}\n\n"
            f"This is likely a bug. Please report it with:\n"
            f"  - The full command you ran\n"
            f"  - This error message\n"
            f"  - Your thumbkit version",
            file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

