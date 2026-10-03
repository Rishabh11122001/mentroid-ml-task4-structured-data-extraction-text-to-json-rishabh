"""Run from the repository root: python extract.py --text '...'"""
import argparse
import json
import sys
from pathlib import Path
from src.extractor import extract

def main():
    parser = argparse.ArgumentParser(description="Extract a validated person JSON using a local LLM")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text")
    group.add_argument("--input", type=Path, help="UTF-8 paragraph file")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--revision", default="main")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--retries", type=int, choices=[0, 1], default=1)
    args = parser.parse_args()
    try:
        text = args.text if args.text is not None else args.input.read_text(encoding="utf-8")
        if not text.strip() or len(text) > 6000:
            raise ValueError("Provide a nonempty short biography (maximum 6000 characters)")
        from src.model import LocalModel
        model = LocalModel(args.model, args.revision, args.threads)
        person, _ = extract(text, model, args.retries)
        result = json.dumps(person.model_dump(), ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(result + "\n", encoding="utf-8")
        print(result)
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
