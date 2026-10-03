"""Small hand-labelled diagnostic benchmark; not a held-out generalization estimate."""
import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from src.extractor import extract, ExtractionError
from src.schema import parse_json

def normalize(value):
    return " ".join(value.casefold().split()) if isinstance(value, str) else value

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/examples.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--revision", default="main")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    cases = [json.loads(line) for line in args.data.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases:
        raise ValueError("No evaluation cases")
    from src.model import LocalModel
    model = LocalModel(args.model, args.revision, args.threads)
    rows = []
    for case in cases:
        started = time.perf_counter()
        error, prediction, attempts = None, None, []
        try:
            person, attempts = extract(case["text"], model)
            prediction = person.model_dump()
        except ExtractionError as exc:
            attempts, error = exc.attempts, str(exc)
        # Unexpected runtime errors deliberately stop evaluation; they are not extraction results.
        matches = {key: prediction is not None and normalize(prediction[key]) == normalize(value)
                   for key, value in case["expected"].items()}
        syntax_valid = False
        if attempts:
            try:
                syntax_valid = isinstance(parse_json(attempts[0]["raw"]), dict)
            except ValueError:
                pass
        rows.append({**case, "prediction": prediction, "attempts": attempts, "error": error,
                     "first_json_object_valid": syntax_valid, "field_matches": matches,
                     "exact_match": all(matches.values()), "seconds": round(time.perf_counter()-started, 3)})
        print(f"{case['id']}: valid={prediction is not None}, correct={all(matches.values())}", flush=True)
    n = len(rows)
    summary = {
        "model": args.model, "model_revision": model.revision,
        "data_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
        "prompt_sha256": hashlib.sha256(Path("src/prompts.py").read_bytes()).hexdigest(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": {p: version(p) for p in ("torch", "transformers", "pydantic")},
        "device": "cpu", "threads": args.threads, "decoding": "greedy", "max_new_tokens": 128,
        "cases": n, "first_attempt_json_object_rate": sum(r["first_json_object_valid"] for r in rows)/n,
        "first_attempt_schema_rate": sum(r["attempts"][0]["valid"] for r in rows)/n,
        "final_schema_rate": sum(r["prediction"] is not None for r in rows)/n,
        "exact_record_accuracy": sum(r["exact_match"] for r in rows)/n,
        "field_accuracy": {k: sum(r["field_matches"][k] for r in rows)/n for k in ("name", "age", "profession")},
        "inference_seconds": round(sum(r["seconds"] for r in rows), 3),
        "note": "Synthetic, hand-labelled diagnostic set; errors count as incorrect. Strings compared after case/whitespace normalization. No synonym matching."
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "predictions.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in rows), encoding="utf-8")
    (args.output_dir / "evaluation.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
