To take this from an initial scraper to a fully functional Sabermetric data pipeline, you need to structure your Python backend into distinct stages. Since you already have experience building data pipelines for your Statcast Spray Chart Pro project, the pandas operations here will feel very familiar.

Here is the complete technical architecture to calculate **Challenge Run Value ($cRV$)**.

**1.Construct the RE288 Static Matrix:**

You need a lookup table that assigns a run expectancy to every single base-out-count combination. Since you are calculating the value of the count changing, standard RE24 isn't enough; you need RE288 (8 base states $\times$ 3 outs $\times$ 12 counts).

You can build this yourself by taking 5 years of historic MLB play-by-play data and averaging the runs scored through the rest of the inning for each state, or download a pre-computed RE288 CSV.

Your table should look like this in pandas:

`['base_state', 'outs', 'count', 'run_expectancy']`

**2.Map Pre- and Post-Challenge States:**

Your script from earlier successfully isolates the challenge events. Now, for every row in `challenges_df`, you need to calculate what the run expectancy _was_ (based on the umpire's original call) and what it _became_(based on the challenge result).

- **Create the Reality Column:** If the umpire called a strike on 1-1, the `post_call_count` is 1-2.
    
- **Create the Challenged Column:** If the challenge overturned it to a ball, the `post_challenge_count` is 2-1.
    
- **Merge:** Do a double `pd.merge()` against your RE288 matrix. First, merge on `post_call_count` to get `RE_Reality`. Then, merge on `post_challenge_count` to get `RE_Challenge`.
    

**3.Calculate the Pitch-Level Delta (\Delta RV_{pitch}):**

This is simple vector math across your dataframe.

Python

```
# If the batter challenged and won:
challenges_df['delta_rv'] = challenges_df['RE_Challenge'] - challenges_df['RE_Reality']

# If the catcher challenged and won, the formula flips (because lowering RE is good for the defense):
challenges_df['delta_rv'] = challenges_df['RE_Reality'] - challenges_df['RE_Challenge']
```

If the challenge failed, `delta_rv` is $0$, because the call stood and the run expectancy did not change.

**4.Apply the Time-Decayed Opportunity Cost:**

This is where you penalize failed challenges based on the inning. You will need to calculate your constant $EV_c$ (Baseline Expected Value of a challenge) based on the league average success rate.

Python

```
# EV_c is your calculated constant (e.g., 0.15 runs)
challenges_df['innings_remaining'] = 9 - challenges_df['inning']

# Floor the innings remaining at 0 for extra innings
challenges_df['innings_remaining'] = challenges_df['innings_remaining'].clip(lower=0)

# Apply the penalty only if the challenge was lost
challenges_df['penalty'] = 0.0
mask_lost = (challenges_df['challenge_success'] == False)
challenges_df.loc[mask_lost, 'penalty'] = -1 * (challenges_df['innings_remaining'] / 9) * EV_c
```

**5.Calculate Final cRV and Aggregate:**

Sum the components to get the final metric for the event, then group the data by player to generate your leaderboards.

Python

```
challenges_df['cRV'] = challenges_df['delta_rv'] + challenges_df['penalty']

# Roll up to the player level
catcher_leaderboard = challenges_df[challenges_df['challenger_type'] == 'catcher'] \
    .groupby(['player_name', 'player_id']) \
    .agg(
        total_challenges=('cRV', 'count'),
        success_rate=('challenge_success', 'mean'),
        cumulative_cRV=('cRV', 'sum')
    ).sort_values(by='cumulative_cRV', ascending=False)
```

Once you have `catcher_leaderboard` outputting a clean dataframe, the heavy lifting is done. You can then export that to a CSV, pull the top 5 and bottom 5 players, and you have the data foundation for the "Results" section of your paper.