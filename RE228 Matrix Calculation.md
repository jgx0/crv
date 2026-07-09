Calculating the RE288 matrix from scratch using `pybaseball` is a fantastic exercise. It requires taking raw pitch data, looking ahead to the end of the inning to see how many runs scored, and then grouping by the exact game state (balls, strikes, outs, and baserunners).

Here is the exact step-by-step logic and the Python code to generate your baseline matrix.

### The Logic Behind RE288

1. **Group by Half-Inning:** Every pitch belongs to a specific half-inning (e.g., Top of the 3rd, Game 710000). You need to find the total runs scored by the batting team by the end of that specific half-inning.
    
2. **Calculate "Runs to End of Inning":** For every individual pitch, subtract the batting team's current score _at the time of the pitch_ from the final score of that half-inning. This gives you the actual runs scored _after_ that specific pitch state.
    
3. **Define the 288 States:** Create a unique state ID for every pitch based on:
    
    - **Outs:** (0, 1, 2)
        
    - **Base State:** 8 possible combinations (Empty, 1B, 2B, 3B, 1B/2B, 1B/3B, 2B/3B, Loaded)
        
    - **Count:** 12 possible counts (0-0 through 3-2)
        
4. **Average it out:** Group your entire dataset of millions of pitches by those 288 unique states, and take the mean of the "Runs to End of Inning" column.
    

### The Python Implementation

Here is the script to generate the matrix. You will want to run this on at least 3-5 full seasons of data to ensure the rare states (like bases loaded, 0 outs, 3-0 count) have a large enough sample size to stabilize.

Python

```
import pandas as pd
from pybaseball import statcast

def build_re288_matrix(start_date, end_date):
    print(f"Downloading play-by-play data from {start_date} to {end_date}...")
    # 1. Fetch the data
    df = statcast(start_dt=start_date, end_dt=end_date)
    
    # Drop rows where the play isn't fully defined
    df = df.dropna(subset=['events', 'balls', 'strikes', 'outs_when_up', 'bat_score', 'post_bat_score'])
    
    print("Calculating inning run totals...")
    # 2. Map the base runners to a boolean state
    for base in ['1b', '2b', '3b']:
        df[f'on_{base}_bool'] = df[f'on_{base}'].notnull().astype(int)
        
    # Create the 8-state base string (e.g., "100" = runner on 1st, "111" = bases loaded)
    df['base_state'] = (
        df['on_1b_bool'].astype(str) + 
        df['on_2b_bool'].astype(str) + 
        df['on_3b_bool'].astype(str)
    )
    
    # Ensure pitch counts don't exceed normal bounds due to bad data entries (e.g. intentional walks)
    df = df[(df['balls'] <= 3) & (df['strikes'] <= 2)]
    df['count_state'] = df['balls'].astype(str) + "-" + df['strikes'].astype(str)

    # 3. Calculate "Runs Scored from this point to the end of the inning"
    # First, find the maximum score the batting team reached in that specific half inning
    df['inning_final_score'] = df.groupby(
        ['game_pk', 'inning', 'inning_topbot']
    )['post_bat_score'].transform('max')
    
    # Subtract the current score to find how many runs scored *after* this pitch
    df['runs_to_end_of_inning'] = df['inning_final_score'] - df['bat_score']
    
    print("Averaging run expectancy across all 288 states...")
    # 4. Group by the 288 unique states and take the average
    re288_matrix = df.groupby(
        ['outs_when_up', 'base_state', 'count_state']
    ).agg(
        sample_size=('runs_to_end_of_inning', 'count'),
        expected_runs=('runs_to_end_of_inning', 'mean')
    ).reset_index()
    
    return re288_matrix

# Execute the function for a recent season
re288_2025 = build_re288_matrix('2025-03-20', '2025-10-01')

# Check the results for a specific scenario (e.g., Bases Loaded, 0 Outs)
bases_loaded_0_outs = re288_2025[
    (re288_2025['base_state'] == '111') & 
    (re288_2025['outs_when_up'] == 0)
].sort_values(by='expected_runs', ascending=False)

print(bases_loaded_0_outs)
```

### Data Hygiene Note

When you run this script, pay attention to the `sample_size` column in your final matrix.

Pitch states like 0-0 counts with bases empty will have hundreds of thousands of pitches to draw from, making the expected run value incredibly accurate. However, highly leveraged extreme counts (like a 3-0 count with 2 outs and bases loaded) happen very rarely. If the sample size is under 50 pitches, the data might be noisy (e.g., an average of 3.2 expected runs, when the true mathematical value should be 2.9).

Because your paper is analyzing the challenge system—and managers specifically save challenges for those rare, high-leverage situations—using a multi-year baseline for your RE288 matrix is critical to ensuring your $\Delta RV$ calculations are stable.

