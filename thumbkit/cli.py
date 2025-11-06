import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from thumbkit.core import (
    MODEL_NAME,
    generate_image_bytes,
    edit_image_bytes,
    load_default_system_prompt,
    save_image_bytes,
)

load_dotenv()


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
    return Path(env) if env else (Path.cwd() / ".thumbkit-generations")


def cmd_generate(args: argparse.Namespace) -> int:
    system_prompt = _read_text(args.system_prompt) or load_default_system_prompt()
    image_bytes, meta = generate_image_bytes(
        prompt=args.prompt,
        reference_image_paths=args.ref or None,
        system_prompt=system_prompt,
        aspect_ratio=args.aspect,
        model_name=MODEL_NAME,
    )

    out_dir = Path(args.out_dir) if args.out_dir else _default_out_dir()
    file_path = save_image_bytes(image_bytes, out_dir, prefix="thumbkit")

    result = {
        "file_path": file_path,
        "bytes": len(image_bytes),
        "aspect_ratio": meta.get("aspect_ratio", args.aspect),
        "reference_image_paths": meta.get("reference_image_paths", args.ref or []),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Saved to {file_path}")
    return 0


def cmd_edit(args: argparse.Namespace) -> int:
    system_prompt = _read_text(args.system_prompt) or load_default_system_prompt()
    image_bytes, meta = edit_image_bytes(
        prompt=args.prompt,
        base_image_path=args.base,
        reference_image_paths=args.ref or None,
        system_prompt=system_prompt,
        aspect_ratio=args.aspect,
        model_name=MODEL_NAME,
    )

    out_dir = Path(args.out_dir) if args.out_dir else _default_out_dir()
    file_path = save_image_bytes(image_bytes, out_dir, prefix="thumbkit-edit")

    result = {
        "file_path": file_path,
        "bytes": len(image_bytes),
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
    p = argparse.ArgumentParser("thumbkit", description="YouTube thumbnail generator CLI (Gemini)")
    sub = p.add_subparsers(dest="cmd", required=False)

    g = sub.add_parser("generate", help="Generate an image from text and optional reference images")
    g.add_argument("--prompt", required=True, help="Text prompt")
    g.add_argument("--ref", action="append", help="Reference image file path (repeatable)")
    g.add_argument("--aspect", default="16:9", help="Aspect ratio (default: 16:9)")
    g.add_argument("--system-prompt", help="Path to a system prompt file to override default")
    g.add_argument("--out-dir", help="Output directory (default: CWD or $THUMBKIT_OUTPUT_DIR)")
    g.add_argument("--json", action="store_true", help="Print JSON result")
    g.set_defaults(func=cmd_generate)

    e = sub.add_parser("edit", help="Edit an existing image with optional references")
    e.add_argument("--prompt", required=True, help="Edit instructions")
    e.add_argument("--base", required=True, help="Base image path to edit")
    e.add_argument("--ref", action="append", help="Reference image file path (repeatable)")
    e.add_argument("--aspect", default="16:9", help="Aspect ratio (default: 16:9)")
    e.add_argument("--system-prompt", help="Path to a system prompt file to override default")
    e.add_argument("--out-dir", help="Output directory (default: CWD or $THUMBKIT_OUTPUT_DIR)")
    e.add_argument("--json", action="store_true", help="Print JSON result")
    e.set_defaults(func=cmd_edit)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # If no command provided, show help
    if not args.cmd:
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

