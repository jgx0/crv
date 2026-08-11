# Challenge Run Value (cRV) Pipeline

A reproducible sabermetric pipeline that quantifies the strategic value of
Automated Ball-Strike (ABS) challenges in Major League Baseball. It pairs an
RE288 run-expectancy surface with a time-decaying opportunity-cost penalty to
score each batter/catcher challenge in runs, then rolls the events up into
player leaderboards and validation summaries for the accompanying paper.

## What cRV measures

For each challenge event:

```
cRV = ΔRV_pitch + Penalty
```

- **ΔRV_pitch** — the run-expectancy swing from the overturned call.
  Batter-favorable overturns raise RE; catcher-favorable overturns lower it.
  Failed challenges leave the state unchanged, so ΔRV = 0.
- **Penalty** — `-(max(0, 9 - inning) / 9) * EV_c`, applied only to *failed*
  challenges (successful challenges are retained under ABS rules). Extra
  innings reset to zero penalty. `EV_c = 0.15` runs in v1.

Terminal outcomes are modeled properly: **Ball 4** advances runners under force
rules and adds any run forced home; **Strike 3** increments outs (RE = 0 if the
half-inning ends). This is the key correctness fix over earlier drafts, which
zeroed all plate-appearance-ending states and erased the highest-leverage
events.

## Pipeline modules

| Module            | File            | Responsibility                                   |
|-------------------|-----------------|--------------------------------------------------|
| Ingestion         | `ingestion.py`  | Statcast pull via `pybaseball` (2026 ABS window) |
| Event isolation   | `events.py`     | Filter `des` text, infer role/call/success       |
| Alternate realities | `realities.py`| Build umpire-call vs. overturned states          |
| RE288 mapping     | `re288.py`      | Empirical or synthetic RE288 lookup              |
| Scoring           | `calculate.py`  | ΔRV + opportunity-cost penalty                   |
| Validation        | `analysis.py`   | Bootstrap CI, leverage buckets, EV sensitivity   |
| Orchestration     | `pipeline.py`   | End-to-end run + figures/tables                  |

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Full run (falls back to synthetic corpus if Statcast is unreachable)
python pipeline.py --output-dir outputs

# Offline demo with the built-in 10-event synthetic corpus
python pipeline.py --force-synthetic --output-dir outputs

# Tests
python -m pytest tests/ -q
```

## Outputs (`outputs/`)

- `challenge_events_scored.csv` — per-event states, ΔRV, penalty, cRV
- `player_leaderboard.csv` — cumulative/mean cRV by player
- `challenger_summary.csv` — aggregate cRV by role
- `validation_summary.csv` — bootstrap CI for mean cRV
- `leverage_summary.csv` — cRV by inning bucket
- `ev_sensitivity.csv` — total cRV across EV_c ∈ [0.05, 0.30]
- `parse_quality_summary.csv` — event-isolation quality tallies
- `re288_matrix.csv`, `run_metadata.csv` — RE surface and provenance
- `figures/*.svg`, `tables/*.tex` — paper-ready artifacts

`run_metadata.csv` records the data and RE288 source (`statcast`/`synthetic`,
`empirical`/`synthetic`/`csv`) so results are never silently misattributed.

## Paper

`paper/main.tex` is a working draft. Build with:

```bash
cd paper && make paper   # requires a TeX distribution (pdflatex)
```

The paper `\input`s the generated tables, so rerun the pipeline before building.

## Status

Current numbers are a **methodological / systems-validation baseline** on a
designed synthetic corpus. Replacing synthetic inputs with full 2026 Statcast
challenge logs and a multi-season empirical RE288 matrix is the primary
remaining empirical step (see `todo.md`).
