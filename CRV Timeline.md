
## Phase 1: Data Engineering (Weeks 1-2)

This phase is purely about getting the raw information into a usable format.

- **Task 1: The Master Scrape.** Run the `pybaseball` script to pull all 2026 MLB play-by-play data. With the ABS challenge system live across all ballparks, you will have a massive, clean dataset.
    
- **Task 2: Isolate the Events.** Filter the DataFrame down to the exact rows where an ABS challenge was triggered (searching the `des` column).
    
- **Task 3: Build the Matrix.** Calculate the historic RE288 matrix (Runs Expectancy across all 288 base-out-count states) using 3-5 years of prior data to ensure your baseline values are mathematically stable.
    

## Phase 2: Mathematical Modeling (Weeks 3-4)

This is where you build the actual algorithm.

- **Task 4: Calculate the Pitch Delta.** For every challenge, calculate the Run Expectancy of the umpire's initial call, and subtract it from the Run Expectancy of the overturned call. This is your raw $\Delta RV_{pitch}$.
    
- **Task 5: Code the Opportunity Cost.** Establish the baseline Expected Value ($EV_c$) of a challenge. Write the time-decay formula to penalize players who lose challenges early in the game: $-1 \times \left( \frac{\text{Innings Remaining}}{9} \right) \times EV_c$.
    
- **Task 6: The Final Equation.** Merge the raw delta with the time-decay penalty to output the final $cRV$for every single challenge event.
    

## Phase 3: Analysis & Validation (Week 5)

Data is useless without narrative. This phase finds the story your data is telling.

- **Task 7: Generate Leaderboards.** Group the data by player (catchers and batters) to find who generated the most value via challenges, and who hurt their teams the most.
    
- **Task 8: Find the Edge Cases.** Isolate the lowest-leverage challenges and the highest-leverage challenges. Document exactly how your model handled a 9th-inning, bases-loaded challenge versus a 1st-inning 0-0 pitch.
    

## Phase 4: Drafting & Publication (Weeks 6-8)

A completed, rigorous sabermetric paper is a massive differentiator for college applications—especially if you are targeting data-heavy quantitative programs at schools like Vanderbilt or Wake Forest.

- **Task 9: The Write-Up.** Structure the paper formally: Abstract, Introduction, Methodology (show your math), Results (show your leaderboards), and Conclusion. Keep it under 2,000 words.
    
- **Task 10: Community Review.** Post a draft of the methodology and top-10 leaderboards to the FanGraphs Community Research blog or a sabermetrics forum to get peer feedback.
    
- **Task 11: Formal Submission.** Submit the final, polished paper to the SABR Analytics Conference Student Track (abstracts usually due in November) or the SABR Baseball Research Journal.
    

