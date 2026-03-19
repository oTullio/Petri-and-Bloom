"""Re-run alignment_judge scoring on a completed eval log."""

import sys
from dotenv import load_dotenv
load_dotenv()  # load .env before any API clients initialize

import petri  # noqa: F401 — registers petri scorers/tasks in inspect registry

from inspect_ai._eval.score import score
from inspect_ai.log import read_eval_log, write_eval_log
from petri.scorers.judge import alignment_judge

LOG_FILE = "logs/2026-03-19T01-56-26-00-00_audit_avQw8PeAcFo6UUEn5LXery.eval"
JUDGE_MODEL = "google/gemini-3-flash-preview"

if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else LOG_FILE
    judge_model = sys.argv[2] if len(sys.argv) > 2 else JUDGE_MODEL

    print(f"Loading log: {log_file}")
    log = read_eval_log(log_file, header_only=False)

    print(f"Scoring with judge model: {judge_model}")
    scorer = alignment_judge(model=judge_model)
    scored_log = score(log, scorer, action="overwrite")

    write_eval_log(scored_log, log_file)
    print(f"Done. Results written to: {log_file}")
