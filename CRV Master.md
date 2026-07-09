

# System Specification: Challenge Run Value (cRV) Pipeline

## 1. Project Objective

Build a sabermetric data pipeline using `pandas` and `pybaseball` to calculate **Challenge Run Value (cRV)** for the 2026 MLB season. $cRV$ measures the strategic value of a batter or catcher initiating an Automated Ball-Strike (ABS) challenge. It calculates the immediate Run Expectancy (RE) shift of the pitch, adjusted by the game-theoretic opportunity cost of burning a challenge based on the inning leverage.

## 2. Mathematical Framework

The coding agent must implement the following equations mathematically in the DataFrame logic:

**A. The Pitch Delta ($\Delta RV_{pitch}$)**

The run value added or subtracted purely by the change in the pitch count/outcome.

- **If the Batter Challenges and Wins:** $\Delta RV_{pitch} = RE(\text{overturned state}) - RE(\text{original umpire state})$
    
- **If the Catcher Challenges and Wins:** $\Delta RV_{pitch} = RE(\text{original umpire state}) - RE(\text{overturned state})$
    
- **If the Challenge is Lost:** $\Delta RV_{pitch} = 0$ (The pitch outcome does not change).
    

**B. The Baseline Challenge Expected Value ($EV_c$)**

A static constant representing the value of a challenge kept in the pocket.

- $EV_c = P(\text{need}) \times P(\text{win}) \times \text{Avg}(\Delta RV_{late\_game})$
    
- _Implementation Note:_ For V1 of this model, hardcode $EV_c = 0.15$ runs.
    

**C. The Lost Challenge Penalty**

Teams only lose a challenge if they are incorrect. If a challenge is lost, apply a time-decay penalty based on innings remaining ($I_{rem}$).

- **Penalty** $= - \left( \frac{I_{rem}}{9} \right) \times EV_c$
    
- _Edge Case constraint:_ $I_{rem}$ cannot be less than $0$. In extra innings, the penalty is $0$ because teams are granted a free challenge every inning.
    

**D. The Final Equation**

- $cRV = \Delta RV_{pitch} + \text{Penalty}$
    

## 3. Data Schemas

The pipeline requires generating and merging two primary DataFrames.

**Schema A: `re288_matrix` (Static Lookup Table)**

The RE288 matrix maps the run expectancy for all 288 possible game states.

- `base_state` (string): 3-character binary string (e.g., `"100"` = 1B only, `"111"` = Bases Loaded).
    
- `outs` (int): 0, 1, or 2.
    
- `count_state` (string): Format `"B-S"` (e.g., `"0-0"`, `"3-2"`).
    
- `expected_runs` (float): The historic average runs scored from this state to the end of the inning.
    

**Schema B: `challenges_df` (The Action Table)**

The filtered play-by-play Statcast data containing only challenge events.

- `game_date` (datetime)
    
- `inning` (int)
    
- `inning_topbot` (string): "Top" or "Bot"
    
- `challenger_type` (string): "batter" or "catcher"
    
- `challenge_success` (boolean): True if overturned, False if upheld.
    
- `original_count_state` (string)
    
- `overturned_count_state` (string): Calculated via logic (e.g., if original was 1-1 strike, it was 1-2. Overturned makes it 2-1).
    
- `RE_Reality` (float): Merged from `re288_matrix` using original state.
    
- `RE_Challenge` (float): Merged from `re288_matrix` using overturned state.
    
- `cRV` (float): The final calculated metric.
    

## 4. Implementation Pipeline

Instruct your coding agent to build the system strictly according to these sequential modules:

**1.Module 1: Data Ingestion:**Use pybaseball to gather raw inputs.

Write a function `fetch_2026_statcast_data(start_date, end_date)`. Since MLB fully adopted the ABS challenge system in 2026, scrape data from `2026-03-26` onward. Return a Pandas DataFrame.

**2.Module 2: Event Isolation:**Search play-by-play text strings.

Write a function `filter_challenge_events(df)`. Search the `des` (description) column for keywords: `["challenge", "overturned", "upheld", "abs"]`. Create a boolean `challenge_success` column based on whether the string contains "overturned" or "upheld". Parse the description to determine if the `challenger_type` was the batter or catcher.

**3.Module 3: Pre/Post State Generator:**Account for pitch logic and ABS rules.

Write a function `generate_alternate_realities(challenges_df)`. For every challenge event, mathematically determine the `original_count_state` and `overturned_count_state`.

_Rule:_ ABS only challenges balls and strikes. If a batter challenges a called strike on 0-0 and wins, the `overturned_count` is 1-0. If they lose, the `original_count` remains 0-1.

**4.Module 4: Run Expectancy Mapping:**Perform standard pandas merges.

Write a function `map_re288(challenges_df, re288_matrix)`. Perform two left merges against the static RE288 matrix.

1. Merge on `[base_state, outs, original_count_state]` to populate `RE_Reality`.
    
2. Merge on `[base_state, outs, overturned_count_state]` to populate `RE_Challenge`.
    

**5.Module 5: cRV Calculation Engine:**Execute the cRV formulas.

Write a function `calculate_crv(challenges_df)`.

1. Calculate $\Delta RV_{pitch}$ using the formulas in Section 2A.
    
2. Calculate `innings_remaining = max(0, 9 - inning)`.
    
3. Calculate the Lost Challenge Penalty (only if `challenge_success == False`).
    
4. Sum them to create the final `cRV` column.
    

## 5. Required Edge Case Handling

The coding agent MUST include logical constraints in Module 5 to handle the following:

1. **The Strike 3 / Ball 4 Inning Ender:** If a pitch outcome results in a strikeout that ends the inning, the resulting `RE_Reality` or `RE_Challenge` must manually be set to `0.0`. It cannot query the RE288 matrix for "3 outs".
    
2. **The Base Advancement Rule:** If a pitch results in Ball 4, the model must account for the `base_state`changing (e.g., runners moving up) when querying the resulting Run Expectancy.
    
3. **Low-Leverage Overturns:** If a player successfully challenges a 0-0 pitch, the $\Delta RV$ will be very small (e.g., +0.03 runs). The agent must ensure that NO penalty is applied to this row, as successful challenges are retained by the team.