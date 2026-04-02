"""Re-run alignment_judge scoring on completed eval logs.

Usage:
    .venv/bin/python rescore.py logs/some_log.eval [logs/other_log.eval ...] [--judge-model MODEL]
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # load .env before any API clients initialize

import petri  # noqa: F401 — registers petri scorers/tasks in inspect registry

from inspect_ai._eval.score import score
from inspect_ai.log import read_eval_log, write_eval_log
from petri.scorers.judge import alignment_judge

from animal_welfare_judge import ANIMAL_WELFARE_DIMENSIONS

JUDGE_MODEL = "google/gemini-3.1-flash-lite-preview"


def rescore_log(log_file: str, judge_model: str) -> dict:
    """Rescore a single log file and return summary of scores."""
    print(f"\n{'='*60}")
    print(f"Loading log: {log_file}")
    log = read_eval_log(log_file, header_only=False)
    print(f"  Samples: {len(log.samples) if log.samples else 0}")

    print(f"  Scoring with judge model: {judge_model}")
    scorer = alignment_judge(dimensions=ANIMAL_WELFARE_DIMENSIONS, model=judge_model)
    scored_log = score(log, scorer, action="append")

    write_eval_log(scored_log, log_file)
    print(f"  Scores written back to: {log_file}")

    # Build readable summary
    summary = {"log_file": log_file, "judge_model": judge_model, "samples": []}
    for sample in scored_log.samples or []:
        sample_summary = {"id": sample.id}
        # Find the animal welfare scorer (the appended one)
        for scorer_name, score_val in (sample.scores or {}).items():
            if isinstance(score_val.value, dict):
                # Check if this scorer has our animal welfare dimensions
                has_aw = any(k in score_val.value for k in ANIMAL_WELFARE_DIMENSIONS)
                if has_aw:
                    sample_summary["scorer"] = scorer_name
                    sample_summary["scores"] = score_val.value
        summary["samples"].append(sample_summary)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rescore one or more completed eval logs with the animal welfare judge."
    )
    parser.add_argument(
        "logs",
        nargs="*",
        help="One or more .eval log files to rescore.",
    )
    parser.add_argument(
        "--judge-model",
        default=JUDGE_MODEL,
        help=f"Judge model to use (default: {JUDGE_MODEL}).",
    )
    args = parser.parse_args()

    if not args.logs:
        parser.print_usage(sys.stderr)
        sys.stderr.write("rescore.py: error: provide at least one log file to rescore\n")
        raise SystemExit(2)

    all_summaries = []
    for log_file in args.logs:
        summary = rescore_log(log_file, args.judge_model)
        all_summaries.append(summary)

    # Write readable JSON summary
    output_path = Path("outputs/animal_welfare_rescore_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_summaries, f, indent=2)
    print(f"\n{'='*60}")
    print(f"Readable summary written to: {output_path}")

    # Print quick overview
    for summary in all_summaries:
        print(f"\n--- {summary['log_file']} ---")
        for sample in summary["samples"]:
            scores = sample.get("scores", {})
            if scores:
                avg = sum(scores.values()) / len(scores) if scores else 0
                print(f"  Sample {sample['id']}: avg={avg:.1f}  {scores}")
