"""Compare Logic-LM against direct prompting with the same local model.

Usage:
  python evaluate.py course_kb                 # the Task 4 KB questions (14)
  python evaluate.py prontoqa --limit 50       # first 50 ProntoQA dev problems
Results go to results/<dataset>_<model>.json and a summary is printed.
"""
import argparse
import json
import time
from pathlib import Path

from logic_lm import DEFAULT_MODEL, direct, logic_lm

HERE = Path(__file__).parent


def load(dataset, limit):
    if dataset == "course_kb":
        probs = json.loads((HERE / "data" / "course_kb.json").read_text())
        closed_world = True
    else:
        raw = json.loads((HERE / "data" / "prontoqa_dev.json").read_text())
        probs = [{"id": r["id"], "context": r["context"],
                  "question": r["question"],
                  "answer": "True" if r["answer"] == "A" else "False"} for r in raw]
        closed_world = False
    return probs[:limit] if limit else probs, closed_world


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", choices=["course_kb", "prontoqa"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--refinements", type=int, default=2)
    args = ap.parse_args()

    probs, closed_world = load(args.dataset, args.limit)
    out = HERE / "results" / f"{args.dataset}_{args.model.replace(':', '-')}.json"
    out.parent.mkdir(exist_ok=True)
    partial = out.with_suffix(".partial.jsonl")
    rows = [json.loads(ln) for ln in partial.read_text().splitlines()] if partial.exists() else []
    done = {r["id"] for r in rows}
    for i, p in enumerate(probs, 1):
        if p["id"] in done:
            continue
        t0 = time.time()
        trace = logic_lm(p["context"], p["question"], args.model,
                         max_refinements=args.refinements, closed_world=closed_world)
        base = direct(p["context"], p["question"], args.model)
        rows.append({
            "id": p["id"], "question": p["question"], "gold": p["answer"],
            "logic_lm": trace.answer, "status": trace.status,
            "direct": base, "programs": trace.programs, "errors": trace.errors,
            "seconds": round(time.time() - t0, 1),
        })
        with partial.open("a") as f:
            f.write(json.dumps(rows[-1]) + "\n")
        print(f"[{i}/{len(probs)}] gold={p['answer']:<5} logic_lm={trace.answer:<7} "
              f"direct={base:<7} {trace.status} ({time.time() - t0:.0f}s)", flush=True)

    n = len(rows)
    solved_first = sum(r["status"] == "solved" for r in rows)
    solved_any = sum(r["status"].startswith("solved") for r in rows)
    summary = {
        "dataset": args.dataset, "model": args.model, "n": n,
        "logic_lm_accuracy": sum(r["logic_lm"] == r["gold"] for r in rows) / n,
        "direct_accuracy": sum(r["direct"] == r["gold"] for r in rows) / n,
        "executable_rate_no_refinement": solved_first / n,
        "executable_rate_with_refinement": solved_any / n,
        "executable_accuracy": (sum(r["logic_lm"] == r["gold"] for r in rows
                                    if r["status"].startswith("solved")) / solved_any) if solved_any else 0,
    }
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    partial.unlink()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
