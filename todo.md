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

## Done (2026 real-data analysis)
- [x] Replace synthetic fallback with full 2026 Statcast challenge extraction
      (1,914 real events; events.py parses the "challenged (pitch result)"
      grammar).
- [x] Report per-cell RE288 sample sizes (`re288_sample_summary.csv`): 288 cells,
      median 574, 29 cells < 100 pitches.
- [x] Estimate EV_c empirically as P(need) x P(win) x mean late-game ΔRV
      (`ev_c_estimate.csv`): 0.204 x 0.460 x 0.357 = 0.033 runs, cluster-
      bootstrap CI [0.029, 0.038].
- [x] Add a win-probability (WPA) overlay on successful overturns
      (`challenge_wpa_summary.csv`): catchers +14.5 vs batters +5.5 win prob.

## Remaining empirical work
- [ ] Build multi-season empirical RE288 matrix (single-season only so far).
- [ ] Validate challenge parsing rules against real ABS game logs and correct
      false positives/negatives.
- [ ] Refine the empirical EV_c estimate with an option-value model.
- [ ] Add year-over-year stability / split-half reliability for player cRV once
      multi-season ABS records are available.
- [ ] Extend the WPA overlay into a full WPA-denominated model (win-denominated
      penalty).
