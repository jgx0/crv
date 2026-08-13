"""Validation/statistical summaries for CRV experiments."""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

try:
    from .calculate import EV_C
except ImportError:  # pragma: no cover
    from calculate import EV_C

# Bootstrap resampling seed. Fixed so the reported confidence intervals are
# reproducible: the paper cites the CI bounds in prose, and an unseeded RNG
# made the table disagree with the text on every re-run.
BOOTSTRAP_SEED = 20260810


def _bootstrap_mean_ci(
    values: pd.Series, n_boot: int = 1000, alpha: float = 0.05, seed: int = BOOTSTRAP_SEED
) -> tuple[float, float]:
    sample = pd.to_numeric(values, errors="coerce").dropna()
    if sample.empty:
        return 0.0, 0.0
    if len(sample) == 1:
        value = float(sample.iloc[0])
        return value, value

    rng = np.random.default_rng(seed)
    arr = sample.to_numpy(dtype=float)
    draws = rng.choice(arr, size=(n_boot, len(arr)), replace=True).mean(axis=1)
    lower = float(np.quantile(draws, alpha / 2))
    upper = float(np.quantile(draws, 1 - alpha / 2))
    return lower, upper


def _cluster_bootstrap_mean_ci(
    df: pd.DataFrame,
    value_col: str = "cRV",
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """Game-level cluster bootstrap CI for a mean.

    Challenges within a game are not independent (a team that challenges
    repeatedly in one game contributes correlated events), so resampling
    events i.i.d. understates uncertainty. Resampling whole games preserves the
    within-game structure. Falls back to the event-level bootstrap when no
    game identifier is present.
    """
    if df is None or df.empty or "game_pk" not in df.columns:
        return _bootstrap_mean_ci(df[value_col] if df is not None else pd.Series(dtype=float), n_boot=n_boot, alpha=alpha, seed=seed)

    sub = df[[value_col, "game_pk"]].copy()
    sub[value_col] = pd.to_numeric(sub[value_col], errors="coerce")
    sub = sub.dropna(subset=[value_col])
    if sub.empty:
        return 0.0, 0.0

    groups = [np.asarray(v, dtype=float) for v in sub.groupby("game_pk")[value_col].apply(list)]
    if len(groups) == 1:
        value = float(np.concatenate(groups).mean())
        return value, value

    rng = np.random.default_rng(seed)
    draws = np.empty(n_boot, dtype=float)
    gidx = np.arange(len(groups))
    for i in range(n_boot):
        picks = rng.choice(gidx, size=len(gidx), replace=True)
        draws[i] = np.concatenate([groups[p] for p in picks]).mean()
    return float(np.quantile(draws, alpha / 2)), float(np.quantile(draws, 1 - alpha / 2))


def build_validation_summary(scored_df: pd.DataFrame, n_boot: int = 1000) -> pd.DataFrame:
    """Compute basic validation metrics and uncertainty summaries."""
    if scored_df is None or scored_df.empty:
        return pd.DataFrame(
            [
                {
                    "metric": "Total events",
                    "value": 0.0,
                    "ci_lower": 0.0,
                    "ci_upper": 0.0,
                    "notes": "No rows available",
                }
            ]
        )

    total_events = float(len(scored_df))
    success_rate = float(pd.to_numeric(scored_df["challenge_success"], errors="coerce").fillna(0).mean())
    mean_crv = float(pd.to_numeric(scored_df["cRV"], errors="coerce").fillna(0.0).mean())
    ci_low, ci_high = _cluster_bootstrap_mean_ci(scored_df, value_col="cRV", n_boot=n_boot)

    return pd.DataFrame(
        [
            {"metric": "Total events", "value": total_events, "ci_lower": total_events, "ci_upper": total_events, "notes": "Count of challenge events"},
            {"metric": "Success rate", "value": success_rate, "ci_lower": 0.0, "ci_upper": 1.0, "notes": "Share of successful challenges"},
            {"metric": "Mean cRV", "value": mean_crv, "ci_lower": ci_low, "ci_upper": ci_high, "notes": "Game-clustered bootstrap CI for mean cRV"},
        ]
    )


def build_leverage_summary(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize cRV by inning-derived leverage buckets."""
    if scored_df is None or scored_df.empty:
        return pd.DataFrame(columns=["leverage_bucket", "events", "mean_cRV", "sum_cRV"])

    df = scored_df.copy()
    df["inning"] = pd.to_numeric(df.get("inning", 9), errors="coerce").fillna(9).astype(int)
    df["leverage_bucket"] = pd.cut(
        df["inning"],
        bins=[0, 3, 6, 9, 99],
        labels=["early(1-3)", "mid(4-6)", "late(7-9)", "extra(10+)"],
        include_lowest=True,
        right=True,
    )

    return (
        df.groupby("leverage_bucket", dropna=False)
        .agg(events=("cRV", "count"), mean_cRV=("cRV", "mean"), sum_cRV=("cRV", "sum"))
        .reset_index()
    )


def build_ev_sensitivity(base_scored_df: pd.DataFrame, ev_values: Iterable[float]) -> pd.DataFrame:
    """Recalculate aggregate cRV under a range of EV_c assumptions."""
    if base_scored_df is None or base_scored_df.empty:
        return pd.DataFrame(columns=["ev_c", "mean_cRV", "sum_cRV"])

    rows = []
    for ev in ev_values:
        modified = base_scored_df.copy()
        failed = modified.get("challenge_success") == False
        weight = (
            modified["penalty_weight"]
            if "penalty_weight" in modified.columns
            else pd.Series(1.0, index=modified.index)
        )
        modified["penalty"] = 0.0
        modified.loc[failed, "penalty"] = (
            -((modified.loc[failed, "innings_remaining"]) / 9.0) * float(ev) * weight.loc[failed]
        )
        modified["cRV"] = modified["delta_rv_pitch"] + modified["penalty"]
        rows.append(
            {
                "ev_c": float(ev),
                "mean_cRV": float(modified["cRV"].mean()),
                "sum_cRV": float(modified["cRV"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("ev_c")


def default_ev_grid(empirical_ev_c: float | None = None) -> list[float]:
    """Provide a compact default EV_c sensitivity grid.

    When an empirical point estimate is supplied it is folded into the grid, so
    the sensitivity sweep always spans the data-driven value as well as the
    fixed range.
    """
    grid = [0.05, 0.10, EV_C, 0.20, 0.25, 0.30]
    if empirical_ev_c is not None:
        grid.append(float(empirical_ev_c))
    return sorted({round(v, 4) for v in grid})


# --- Empirical EV_c estimation ---------------------------------------------

# The opportunity cost of a retained challenge is the value of the challenge a
# team expects to want again later. "Late game" is the seventh inning onward,
# matching the leverage buckets used elsewhere (early 1-3, mid 4-6, late 7-9,
# extra 10+).
LATE_INNING_MIN = 7


def _challenger_side(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Attribute each challenge to the side that issued it.

    A batter challenge is made on behalf of the batting team; a catcher
    challenge on behalf of the fielding team. ``inning_topbot`` tells us which
    side is batting, so the challenging team's abbreviation and home flag fall
    out directly. Rows whose role was not parsed return NaN for both.

    Returns ``(team_abbr, challenger_is_home)``.
    """
    home = df["home_team"].astype(str)
    away = df["away_team"].astype(str)
    batting_is_home = df["inning_topbot"].astype(str).str.upper().str.strip().eq("BOT")
    role = df["challenger_type"].astype(str).str.lower()
    is_batter = role.eq("batter")
    is_catcher = role.eq("catcher")
    known = is_batter | is_catcher

    challenger_is_home = (is_batter & batting_is_home) | (is_catcher & ~batting_is_home)
    team = home.where(challenger_is_home, away).where(known)
    return team, challenger_is_home.where(known)


def _ev_c_game_aggregates(df: pd.DataFrame, value_col: str = "delta_rv_pitch") -> pd.DataFrame:
    """Per-game aggregates that fully determine the EV_c factor estimates.

    Aggregating first lets the cluster bootstrap resample games (not events),
    which preserves the within-game challenge structure that ``P(need)``
    depends on. ``value_col`` is the quantity summed over successful late-game
    challenges -- runs for the run-denominated EV_c, win probability for the
    win-denominated analog.
    """
    team = _challenger_side(df)[0]
    work = df.copy()
    work["_team"] = team.values
    for col in ("inning", "at_bat_number", "pitch_number"):
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)
        else:
            work[col] = 0
    work = work.sort_values(["game_pk", "inning", "at_bat_number", "pitch_number"])

    # A challenge has "future need" if it is not the challenging team's last
    # challenge of the game.
    work["_is_last"] = work.groupby(["game_pk", "_team"], dropna=False).cumcount(ascending=False) == 0
    work["_nonlast"] = (~work["_is_last"]).astype(float)

    success = pd.to_numeric(work["challenge_success"], errors="coerce").fillna(0).astype(float)
    late_success = ((work["inning"] >= LATE_INNING_MIN) & (success == 1.0))
    work["_success"] = success
    work["_late_success"] = late_success.astype(float)
    value = pd.to_numeric(work[value_col], errors="coerce").fillna(0.0)
    work["_late_value"] = value.where(late_success, 0.0)

    return work.groupby("game_pk").agg(
        n=("game_pk", "size"),
        n_success=("_success", "sum"),
        n_nonlast=("_nonlast", "sum"),
        n_late_success=("_late_success", "sum"),
        sum_late_value=("_late_value", "sum"),
    )


def _ev_c_factors(agg: pd.DataFrame) -> tuple[float, float, float, float]:
    """Reduce per-game aggregates to (P_need, P_win, mean_late_value, EV_c)."""
    n = float(agg["n"].sum())
    p_need = float(agg["n_nonlast"].sum() / n) if n else 0.0
    p_win = float(agg["n_success"].sum() / n) if n else 0.0
    n_late = float(agg["n_late_success"].sum())
    mean_late = float(agg["sum_late_value"].sum() / n_late) if n_late else 0.0
    return p_need, p_win, mean_late, p_need * p_win * mean_late


def _signed_win_swing(df: pd.DataFrame) -> pd.Series:
    """Statcast's home-team win-probability swing, signed to the challenger."""
    swing = pd.to_numeric(df["delta_home_win_exp"], errors="coerce").fillna(0.0)
    _, is_home = _challenger_side(df)
    return swing.where(is_home.fillna(False), -swing)


def _estimate_ev_c(
    scored_df: pd.DataFrame,
    value_col: str,
    mean_label: str,
    ev_label: str,
    n_boot: int,
    seed: int,
) -> pd.DataFrame:
    """Shared three-factor EV_c estimator for run- and win-denominated value."""
    if scored_df is None or scored_df.empty:
        return pd.DataFrame(columns=["metric", "value", "ci_lower", "ci_upper"])

    required = {"game_pk", "inning_topbot", "home_team", "away_team", "challenger_type", "challenge_success", value_col}
    if not required.issubset(set(scored_df.columns)):
        return pd.DataFrame(columns=["metric", "value", "ci_lower", "ci_upper"])

    agg = _ev_c_game_aggregates(scored_df, value_col)
    p_need, p_win, mean_late, ev_c = _ev_c_factors(agg)

    # Cluster bootstrap every factor so the table carries a real CI per row,
    # not just for the product.
    factors = [
        ("P(future need)", p_need),
        ("P(win)", p_win),
        (mean_label, mean_late),
        (ev_label, ev_c),
    ]
    ci = {name: (value, value) for name, value in factors}
    if len(agg) > 1:
        rng = np.random.default_rng(seed)
        draws = np.empty((n_boot, len(factors)), dtype=float)
        game_ids = agg.index.to_numpy()
        for i in range(n_boot):
            picks = rng.choice(game_ids, size=len(game_ids), replace=True)
            draws[i] = _ev_c_factors(agg.loc[picks])
        for j, (name, _) in enumerate(factors):
            ci[name] = (
                float(np.quantile(draws[:, j], 0.025)),
                float(np.quantile(draws[:, j], 0.975)),
            )

    return pd.DataFrame(
        [
            {"metric": "P(future need)", "value": p_need, "ci_lower": ci["P(future need)"][0], "ci_upper": ci["P(future need)"][1]},
            {"metric": "P(win)", "value": p_win, "ci_lower": ci["P(win)"][0], "ci_upper": ci["P(win)"][1]},
            {"metric": mean_label, "value": mean_late, "ci_lower": ci[mean_label][0], "ci_upper": ci[mean_label][1]},
            {"metric": ev_label, "value": ev_c, "ci_lower": ci[ev_label][0], "ci_upper": ci[ev_label][1]},
        ]
    )


def estimate_ev_c_empirical(
    scored_df: pd.DataFrame,
    n_boot: int = 1000,
    seed: int = BOOTSTRAP_SEED,
) -> pd.DataFrame:
    """Estimate the run-denominated EV_c as P(need) x P(win) x mean late DeltaRV.

    The three factors mirror the decomposition in the paper's methodology:

    * ``P(need)`` -- the share of challenges that are not the challenging
      team's last challenge of the game (i.e. the team wants a challenge again).
    * ``P(win)`` -- the empirical challenge success rate.
    * ``mean late-game DeltaRV`` -- the mean run delta of successful challenges
      from the seventh inning onward.

    A game-level cluster bootstrap supplies a CI on each factor, because
    ``P(need)`` is defined on the within-game challenge sequence and cannot be
    bootstrapped at the event level.
    """
    return _estimate_ev_c(scored_df, "delta_rv_pitch", "Mean late-game delta RV", "Empirical EV_c", n_boot, seed)


def estimate_ev_c_win(
    scored_df: pd.DataFrame,
    n_boot: int = 1000,
    seed: int = BOOTSTRAP_SEED,
) -> pd.DataFrame:
    """Estimate the win-denominated EV_c as P(need) x P(win) x mean late win swing.

    The win-denominated analog of ``estimate_ev_c_empirical``: the third factor
    is the mean win-probability swing of successful late-game overturns, signed
    to the challenging team. The product is the win-probability value of
    retaining a challenge, used as the penalty constant in the full cWPA model.
    """
    if scored_df is None or scored_df.empty or "delta_home_win_exp" not in scored_df.columns:
        return pd.DataFrame(columns=["metric", "value", "ci_lower", "ci_upper"])
    df = scored_df.copy()
    df["_signed_win_swing"] = _signed_win_swing(df)
    return _estimate_ev_c(df, "_signed_win_swing", "Mean late-game win swing", "Win-denominated EV_c", n_boot, seed)


def build_re288_sample_summary(re288_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize per-cell sample sizes of the empirical RE288 surface.

    Rare base-out-count states (e.g. 3-0 with the bases loaded) are estimated
    from few pitches, so the distribution of ``sample_size`` across the 288
    cells is the honest measure of how stable the surface is.
    """
    if re288_df is None or re288_df.empty or "sample_size" not in re288_df.columns:
        return pd.DataFrame(columns=["metric", "value"])

    n = pd.to_numeric(re288_df["sample_size"], errors="coerce").dropna()
    if n.empty:
        return pd.DataFrame(columns=["metric", "value"])

    return pd.DataFrame(
        [
            {"metric": "RE288 cells", "value": float(len(n))},
            {"metric": "Min pitches per cell", "value": float(n.min())},
            {"metric": "Median pitches per cell", "value": float(n.median())},
            {"metric": "Mean pitches per cell", "value": float(n.mean())},
            {"metric": "Max pitches per cell", "value": float(n.max())},
            {"metric": "Cells under 100 pitches", "value": float((n < 100).sum())},
            {"metric": "Cells under 1000 pitches", "value": float((n < 1000).sum())},
        ]
    )


def build_challenge_wpa_summary(scored_df: pd.DataFrame, ev_c_win: float | None = None) -> pd.DataFrame:
    """Summarize the full win-denominated challenge value (cWPA) by role.

    cWPA parallels cRV in win-probability units:

    * a successful overturn is priced by its win-probability swing
      (``delta_home_win_exp`` signed to the challenging team);
    * a failed challenge changes nothing on the field and instead carries a
      win-denominated opportunity-cost penalty
      ``-(innings_remaining / 9) * EV_c_win``.

    ``EV_c_win`` is the win-probability value of retaining a challenge,
    estimated empirically as P(need) x P(win) x mean late-game win swing unless
    an explicit value is passed in.
    """
    if scored_df is None or scored_df.empty:
        return pd.DataFrame(columns=["challenger_type", "events", "total_wpa", "mean_wpa"])

    required = {"home_team", "away_team", "inning_topbot", "challenger_type", "challenge_success", "delta_home_win_exp", "inning"}
    if not required.issubset(set(scored_df.columns)):
        return pd.DataFrame(columns=["challenger_type", "events", "total_wpa", "mean_wpa"])

    df = scored_df.copy()
    swing = _signed_win_swing(df)
    success = pd.to_numeric(df["challenge_success"], errors="coerce").fillna(0).astype(bool)

    if ev_c_win is None:
        ev_c_win = 0.0
        if "game_pk" in df.columns:
            tmp = df.copy()
            tmp["_signed_win_swing"] = swing.values
            ev_c_win = _ev_c_factors(_ev_c_game_aggregates(tmp, "_signed_win_swing"))[3]

    inning = pd.to_numeric(df["inning"], errors="coerce").fillna(9).astype(int)
    innings_remaining = (9 - inning).clip(lower=0)
    weight = df["penalty_weight"] if "penalty_weight" in df.columns else 1.0
    penalty = np.where(success, 0.0, -(innings_remaining / 9.0) * float(ev_c_win) * weight)

    # Only successful overturns move win probability; failures carry the
    # penalty above and change nothing on the field.
    df["_wpa"] = swing.where(success, 0.0) + penalty

    return (
        df.groupby("challenger_type", dropna=False)
        .agg(events=("_wpa", "size"), total_wpa=("_wpa", "sum"), mean_wpa=("_wpa", "mean"))
        .reset_index()
        .sort_values("total_wpa", ascending=False)
    )


def build_crv_success_correlation(scored_df: pd.DataFrame, min_challenges: int = 10) -> pd.DataFrame:
    """Correlate player-level mean cRV with player challenge success rate.

    If cRV were nearly redundant with accuracy, this correlation would sit
    close to 1; a moderate value shows the metric carries leverage/timing
    information that the raw success rate does not.
    """
    if scored_df is None or scored_df.empty or "player_name" not in scored_df.columns:
        return pd.DataFrame(columns=["metric", "value"])

    df = scored_df.copy()
    df["_crv"] = pd.to_numeric(df["cRV"], errors="coerce").fillna(0.0)
    df["_succ"] = pd.to_numeric(df["challenge_success"], errors="coerce").fillna(0).astype(float)
    g = (
        df.groupby("player_name")
        .agg(n=("_crv", "size"), mean_crv=("_crv", "mean"), success_rate=("_succ", "mean"))
        .query(f"n >= {min_challenges}")
    )
    if len(g) < 3:
        return pd.DataFrame(columns=["metric", "value"])

    r = float(g["mean_crv"].corr(g["success_rate"]))
    rho = float(g["mean_crv"].corr(g["success_rate"], method="spearman"))
    return pd.DataFrame(
        [
            {"metric": "Qualifying players", "value": float(len(g))},
            {"metric": "Min challenges per player", "value": float(min_challenges)},
            {"metric": "Pearson r (cRV vs success rate)", "value": r},
            {"metric": "Spearman rho (cRV vs success rate)", "value": rho},
        ]
    )


def build_split_half_reliability(scored_df: pd.DataFrame, min_challenges_per_half: int = 4) -> pd.DataFrame:
    """Split-half reliability of player-level mean cRV within 2026.

    Splits the season-to-date at its median game date and correlates each
    player's mean cRV across the two halves. A substantial positive
    correlation is evidence that challenge judgment is a stable skill rather
    than noise.
    """
    if scored_df is None or scored_df.empty:
        return pd.DataFrame(columns=["metric", "value"])
    if "game_date" not in scored_df.columns or "player_name" not in scored_df.columns:
        return pd.DataFrame(columns=["metric", "value"])

    df = scored_df.copy()
    df["_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df.dropna(subset=["_date"])
    if df.empty:
        return pd.DataFrame(columns=["metric", "value"])

    median_date = df["_date"].median()
    df["_half"] = np.where(df["_date"] < median_date, "first", "second")
    df["_crv"] = pd.to_numeric(df["cRV"], errors="coerce").fillna(0.0)

    means = df.pivot_table(index="player_name", columns="_half", values="_crv", aggfunc="mean")
    counts = df.pivot_table(index="player_name", columns="_half", values="_crv", aggfunc="count")
    for half in ("first", "second"):
        if half not in counts.columns:
            counts[half] = 0
    keep = (counts["first"] >= min_challenges_per_half) & (counts["second"] >= min_challenges_per_half)
    means = means.loc[keep].dropna()
    if len(means) < 3:
        return pd.DataFrame(columns=["metric", "value"])

    r = float(means["first"].corr(means["second"]))
    rho = float(means["first"].corr(means["second"], method="spearman"))
    return pd.DataFrame(
        [
            {"metric": "Qualifying players", "value": float(len(means))},
            {"metric": "Min challenges per half", "value": float(min_challenges_per_half)},
            {"metric": "Pearson r (split-half cRV)", "value": r},
            {"metric": "Spearman rho (split-half cRV)", "value": rho},
        ]
    )
