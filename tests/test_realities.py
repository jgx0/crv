"""Unit tests for alternate-reality generation and walk/K edge cases."""
from __future__ import annotations

import pandas as pd

from realities import advance_bases_on_walk, generate_alternate_realities
from re288 import load_re288_matrix, map_re288
from calculate import calculate_crv
from events import filter_challenge_events


def test_walk_force_chain_bases_loaded():
    new_state, runs = advance_bases_on_walk("111")
    assert new_state == "111"
    assert runs == 1


def test_walk_runner_on_first_only():
    new_state, runs = advance_bases_on_walk("100")
    assert new_state == "110"
    assert runs == 0


def test_walk_runner_on_second_unforced():
    new_state, runs = advance_bases_on_walk("010")
    assert new_state == "110"
    assert runs == 0


def test_walk_empty_bases():
    new_state, runs = advance_bases_on_walk("000")
    assert new_state == "100"
    assert runs == 0


def test_strikeout_inning_ender_has_zero_re():
    df = pd.DataFrame(
        [
            {
                "des": "Catcher challenge overturned called ball",
                "balls": 3,
                "strikes": 2,
                "outs": 2,
                "on_1b": 1,
                "on_2b": 2,
                "on_3b": None,
                "inning": 9,
                "challenge_success": True,
                "challenger_type": "catcher",
                "called_pitch_type": "called_ball",
                "player_name": "C",
            }
        ]
    )
    realities = generate_alternate_realities(df)
    assert bool(realities.iloc[0]["overturned_inning_over"]) is True
    assert int(realities.iloc[0]["overturned_outs"]) == 3

    mapped = map_re288(realities, load_re288_matrix())
    # Catcher converts walk into inning-ending K: RE_Challenge should be 0.
    assert float(mapped.iloc[0]["RE_Challenge"]) == 0.0
    # Original walk leaves runners on with 2 outs — positive RE.
    assert float(mapped.iloc[0]["RE_Reality"]) > 0.0

    scored = calculate_crv(mapped)
    # Catcher success: RE_Reality - RE_Challenge > 0
    assert float(scored.iloc[0]["cRV"]) > 0.0


def test_bases_loaded_walk_scores_run_and_keeps_re():
    df = pd.DataFrame(
        [
            {
                "des": "Batter challenge overturned called strike",
                "balls": 3,
                "strikes": 2,
                "outs": 1,
                "on_1b": 1,
                "on_2b": 2,
                "on_3b": 3,
                "inning": 4,
                "challenge_success": True,
                "challenger_type": "batter",
                "called_pitch_type": "called_strike",
                "player_name": "B",
            }
        ]
    )
    realities = generate_alternate_realities(df)
    row = realities.iloc[0]
    # Original: strikeout (outs -> 2), overturned: walk (run scores, bases still loaded)
    assert bool(row["original_terminal"]) is True
    assert bool(row["overturned_terminal"]) is True
    assert int(row["overturned_runs_on_play"]) == 1
    assert str(row["overturned_base_state"]) == "111"
    assert int(row["original_outs"]) == 2

    mapped = map_re288(realities, load_re288_matrix())
    # Walk value includes the immediate run plus post-walk RE.
    assert float(mapped.iloc[0]["RE_Challenge"]) >= 1.0
    scored = calculate_crv(mapped)
    assert float(scored.iloc[0]["delta_rv_pitch"]) > 0.0


def test_failed_challenge_extra_innings_zero_penalty():
    df = pd.DataFrame(
        [
            {
                "des": "Catcher challenge upheld called strike",
                "balls": 1,
                "strikes": 2,
                "outs": 1,
                "on_1b": None,
                "on_2b": None,
                "on_3b": None,
                "inning": 11,
                "challenge_success": False,
                "challenger_type": "catcher",
                "called_pitch_type": "called_strike",
                "player_name": "C",
            }
        ]
    )
    realities = generate_alternate_realities(df)
    mapped = map_re288(realities, load_re288_matrix())
    scored = calculate_crv(mapped)
    assert float(scored.iloc[0]["penalty"]) == 0.0
    assert float(scored.iloc[0]["cRV"]) == 0.0


def test_failed_challenges_weight_by_remaining_stock():
    # Two failures by the same team in one game: the first forfeits a 1/2 share
    # (two challenges held), the second a full share (last challenge).
    df = pd.DataFrame(
        [
            {"game_pk": 1, "inning": 1, "inning_topbot": "Bot", "home_team": "A", "away_team": "B",
             "challenger_type": "catcher", "challenge_success": False,
             "at_bat_number": 1, "pitch_number": 1, "RE_Reality": 0.5, "RE_Challenge": 0.5},
            {"game_pk": 1, "inning": 2, "inning_topbot": "Bot", "home_team": "A", "away_team": "B",
             "challenger_type": "catcher", "challenge_success": False,
             "at_bat_number": 2, "pitch_number": 1, "RE_Reality": 0.5, "RE_Challenge": 0.5},
        ]
    )
    scored = calculate_crv(df)
    assert float(scored.iloc[0]["penalty_weight"]) == 0.5
    assert float(scored.iloc[1]["penalty_weight"]) == 1.0
    assert abs(float(scored.iloc[0]["penalty"]) - (-(8 / 9) * 0.15 * 0.5)) < 1e-9
    assert abs(float(scored.iloc[1]["penalty"]) - (-(7 / 9) * 0.15)) < 1e-9


def test_success_does_not_consume_challenge_budget():
    # A successful challenge (event 1) does not shrink the stock, so the first
    # failure that follows it (event 2) still forfeits only a 1/2 share.
    df = pd.DataFrame(
        [
            {"game_pk": 1, "inning": 1, "inning_topbot": "Bot", "home_team": "A", "away_team": "B",
             "challenger_type": "catcher", "challenge_success": True,
             "at_bat_number": 1, "pitch_number": 1, "RE_Reality": 0.5, "RE_Challenge": 0.5},
            {"game_pk": 1, "inning": 2, "inning_topbot": "Bot", "home_team": "A", "away_team": "B",
             "challenger_type": "catcher", "challenge_success": False,
             "at_bat_number": 2, "pitch_number": 1, "RE_Reality": 0.5, "RE_Challenge": 0.5},
            {"game_pk": 1, "inning": 3, "inning_topbot": "Bot", "home_team": "A", "away_team": "B",
             "challenger_type": "catcher", "challenge_success": False,
             "at_bat_number": 3, "pitch_number": 1, "RE_Reality": 0.5, "RE_Challenge": 0.5},
        ]
    )
    scored = calculate_crv(df)
    assert float(scored.iloc[1]["penalty_weight"]) == 0.5
    assert float(scored.iloc[2]["penalty_weight"]) == 1.0


def test_filter_challenge_events_parses_roles_and_calls():
    # Grammar taken verbatim from 2026 Statcast `des` text. Note that
    # `description` holds the call AFTER the challenge resolves, so the
    # original call is its inverse whenever the verdict is "overturned".
    raw = pd.DataFrame(
        [
            # Batter wins: strike three erased, PA becomes a walk.
            {
                "des": "Cal Raleigh challenged (pitch result), call on the field was overturned: Cal Raleigh walks.",
                "description": "ball",
                "balls": 3, "strikes": 2, "outs": 0,
            },
            # Catcher wins: ball four erased, PA becomes a strikeout.
            {
                "des": "Jonah Heim challenged (pitch result), call on the field was overturned: Kevin McGonigle called out on strikes.",
                "description": "called_strike",
                "balls": 3, "strikes": 2, "outs": 1,
            },
            # Batter loses: original strike three confirmed.
            {
                "des": "Cole Young challenged (pitch result), call on the field was confirmed: Cole Young called out on strikes.",
                "description": "called_strike",
                "balls": 1, "strikes": 2, "outs": 2,
            },
            # Replay review, not an ABS challenge -- must be excluded.
            {
                "des": "Yankees challenged (tag play), call on the field was overturned: Chase Meidroth grounds out.",
                "description": "hit_into_play",
                "balls": 0, "strikes": 0, "outs": 0,
            },
            {
                "des": "Routine groundout to shortstop",
                "description": "hit_into_play",
                "balls": 0, "strikes": 0, "outs": 0,
            },
        ]
    )
    out = filter_challenge_events(raw)

    assert len(out) == 3, "only (pitch result) challenges are ABS events"

    assert out.iloc[0]["challenger_type"] == "batter"
    assert out.iloc[0]["called_pitch_type"] == "called_strike"
    assert bool(out.iloc[0]["challenge_success"]) is True

    assert out.iloc[1]["challenger_type"] == "catcher"
    assert out.iloc[1]["called_pitch_type"] == "called_ball"
    assert bool(out.iloc[1]["challenge_success"]) is True

    assert out.iloc[2]["challenger_type"] == "batter"
    assert out.iloc[2]["called_pitch_type"] == "called_strike"
    assert bool(out.iloc[2]["challenge_success"]) is False
    assert (out["parse_quality"] == "ok").all()


def test_replay_review_is_not_an_abs_challenge():
    raw = pd.DataFrame(
        [
            {"des": f"Yankees challenged ({kind}), call on the field was overturned: runner safe.",
             "description": "hit_into_play", "balls": 0, "strikes": 0, "outs": 0}
            for kind in ("play at 1st", "tag play", "force play", "hit by pitch",
                         "home-plate collision", "catcher interference")
        ]
    )
    assert filter_challenge_events(raw).empty


def test_confirmed_and_upheld_both_mean_the_challenger_lost():
    raw = pd.DataFrame(
        [
            {"des": "A B challenged (pitch result), call on the field was confirmed: A B called out on strikes.",
             "description": "called_strike", "balls": 0, "strikes": 2, "outs": 0},
            {"des": "C D challenged (pitch result), call on the field was upheld: C D called out on strikes.",
             "description": "called_strike", "balls": 0, "strikes": 2, "outs": 0},
        ]
    )
    out = filter_challenge_events(raw)
    assert list(out["challenge_success"]) == [False, False]
    # A lost challenge leaves the umpire's original call standing.
    assert list(out["called_pitch_type"]) == ["called_strike", "called_strike"]


def test_suffixed_names_are_not_misread_as_catcher_challenges():
    # "Jr." ends in a period; a naive outcome-clause regex truncates the name
    # there, so the batter no longer matches and is misclassified as a catcher.
    raw = pd.DataFrame(
        [
            {"des": "Vladimir Guerrero Jr. challenged (pitch result), call on the field was confirmed: Vladimir Guerrero Jr. called out on strikes.",
             "description": "called_strike", "balls": 2, "strikes": 2, "outs": 1},
            {"des": "A.J. Ewing challenged (pitch result), call on the field was confirmed: A.J. Ewing called out on strikes.",
             "description": "called_strike", "balls": 0, "strikes": 2, "outs": 0},
        ]
    )
    out = filter_challenge_events(raw)
    assert list(out["challenger_type"]) == ["batter", "batter"]


def test_missing_verdict_is_flagged_not_dropped():
    # Seen once in July 2026: the verdict clause is absent. The challenge was
    # still spent, so the row must survive and be flagged.
    raw = pd.DataFrame(
        [{"des": "Tyler Heineman challenged (pitch result): Brooks Lee walks.",
          "description": "ball", "balls": 3, "strikes": 1, "outs": 0}]
    )
    out = filter_challenge_events(raw)
    assert len(out) == 1
    assert out.iloc[0]["parse_quality"] != "ok"


def test_null_descriptions_do_not_crash_the_parser():
    # Arrow-backed Statcast columns render missing values as float nan under
    # .astype(str), which previously raised TypeError inside the regex.
    raw = pd.DataFrame(
        [
            {"des": None, "description": "ball", "balls": 0, "strikes": 0, "outs": 0},
            {"des": float("nan"), "description": "ball", "balls": 0, "strikes": 0, "outs": 0},
            {"des": "E F challenged (pitch result), call on the field was overturned: E F walks.",
             "description": "ball", "balls": 3, "strikes": 2, "outs": 0},
        ]
    )
    out = filter_challenge_events(raw)
    assert len(out) == 1
