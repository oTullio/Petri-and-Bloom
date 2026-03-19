# Petri and Bloom — Project Guide

## What is this project?

This repo runs automated behavioral evaluations of LLMs using two Anthropic tools:

- **Bloom** — generates and runs structured behavioral evaluations end-to-end
- **Petri** — runs Inspect-based evaluations with custom scoring logic

The current evaluation tests **animal welfare propensity**: whether models spontaneously notice, weigh, and act on animal welfare considerations in realistic deployment scenarios (based on the Anima International report methodology).

## Bloom

Bloom is a 4-stage automated evaluation pipeline:

| Stage | What it does | Output file |
|---|---|---|
| **Understanding** | Evaluator reads the behavior description, generates an evaluation framework | `bloom-results/{behavior}/understanding.json` |
| **Ideation** | Evaluator generates test scenarios with variations | `bloom-results/{behavior}/ideation.json` |
| **Rollout** | Target model is run through each scenario | `bloom-results/{behavior}/rollout.json` |
| **Judgment** | Judge scores target model responses | `bloom-results/{behavior}/judgment.json` |

### Running Bloom

```bash
source .env

# Full pipeline
.venv/bin/bloom run bloom-data

# Individual stages (useful for resuming)
.venv/bin/bloom understanding bloom-data
.venv/bin/bloom ideation bloom-data
.venv/bin/bloom rollout bloom-data
.venv/bin/bloom judgment bloom-data
```

### Resuming after interruption

Individual stage commands read from existing `bloom-results/` JSON files, so you can resume by running the next incomplete stage:

```bash
# If understanding + ideation finished but rollout did not:
.venv/bin/bloom rollout bloom-data
.venv/bin/bloom judgment bloom-data
```

To resume via WandB (for distributed runs), add to `bloom-data/seed.yaml`:
```yaml
resume: "wandb_run_id"
resume_stage: "rollout"   # stage to resume from
```

### Configuration

Main config: `bloom-data/seed.yaml`

Key parameters:
- `behavior.name` — which behavior definition to load from `bloom-data/behaviors.json`
- `configurable_prompts` — prompt variant (e.g. `"animal-welfare"`)
- `ideation.num_scenarios` / `variation_dimensions` — how many scenarios and axes of variation
- `rollout.num_reps` — repetitions per scenario
- `rollout.modality` — `"simenv"` (simulated environment) or `"conversation"`
- `judgment.num_samples` — judge samples per rollout

Models are defined in `bloom-data/models.json`.

## Petri

Petri runs Inspect-based evaluations. Logs are written to `./logs/` (configured via `INSPECT_LOG_DIR` in `.env`) as `.eval` binary files.

Transcript outputs are written to `./outputs/` as JSON files.

## Environment

All API keys and model provider config are in `.env`. Run `source .env` before any bloom or petri commands.
