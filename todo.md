# CRV project todo

## Done
- [x] Fix terminal walk/strikeout RE logic (Ball 4 force chains + runs scored;
      Strike 3 outs increment / inning-end zeroing) instead of zeroing all
      terminal states.
- [x] Wire empirical RE288 estimation through the pipeline (uses same pbp pull
      when Statcast data is available; synthetic fallback otherwise).
- [x] Expand synthetic challenge corpus to 10 events covering non-terminal,
      walk, strikeout, extra-inning, and parse-ambiguity paths.
- [x] Add unit tests (`tests/`) for walk force chains, terminal RE, extra-inning
      penalty, and event parsing.
- [x] Harden packaging: portable Makefile paths, pinned requirements, expanded
      `.gitignore`, README, `--force-synthetic` flag, run metadata + provenance.
- [x] Expand paper draft: methodology (terminal outcomes), case studies,
      leverage/EV sensitivity tables, discussion, limitations, future work.
- [x] Add formal statistical validation baseline (bootstrap CI, leverage
      subgroup summaries, EV sensitivity).
- [x] Add reproducible manuscript build tooling (LaTeX compile target).
- [x] Expand related-work citations with framing/decision-context references.

## Remaining empirical work
- [ ] Replace synthetic fallback with full 2026 Statcast challenge extraction
      once API access is stable.
- [ ] Build multi-season empirical RE288 matrix and report per-cell sample
      sizes (currently estimated inline from the single pbp pull).
- [ ] Validate challenge parsing rules against real ABS game logs and correct
      false positives/negatives.
- [ ] Estimate EV_c empirically: P(need) x P(win) x mean late-game ΔRV.
- [ ] Add year-over-year stability / split-half reliability for player cRV once
      multi-season ABS records are available.
- [ ] Add win-probability (WPA/leverage-index) overlay on top of run-denominated
      cRV.
