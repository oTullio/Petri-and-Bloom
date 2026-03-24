"""Re-run alignment_judge scoring on a completed eval log.

Usage:
    # Rescore all three logs with animal welfare dimensions:
    .venv/bin/python rescore.py

    # Rescore a specific log:
    .venv/bin/python rescore.py logs/some_log.eval

    # Rescore with a different judge model:
    .venv/bin/python rescore.py logs/some_log.eval google/gemini-2.5-pro-preview
"""

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

LOG_FILES = [
    "logs/2026-03-19T01-56-26-00-00_audit_avQw8PeAcFo6UUEn5LXery.eval",
    "logs/2026-03-22T23-31-18-00-00_audit_XGZ3cEv3PAwXjSMyheTUmS.eval",
    "logs/2026-03-24T19-14-50-00-00_audit_ZCb3BVZvEyvjuavVquv53N.eval",
]
JUDGE_MODEL = "google/gemini-3-flash-preview"


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
    if len(sys.argv) > 1:
        log_files = [sys.argv[1]]
    else:
        log_files = LOG_FILES

    judge_model = sys.argv[2] if len(sys.argv) > 2 else JUDGE_MODEL

    all_summaries = []
    for log_file in log_files:
        summary = rescore_log(log_file, judge_model)
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
