# Project Architecture & AI Philosophy

This document explains the design decisions and mathematical logic behind the Chess Move Recommendation System.

## 1. The Core Philosophy: Practical Human Success
Traditional chess engines like Stockfish are "Black Box" models designed for mathematical perfection. However, Stockfish's top recommendation might be a line that requires 20 moves of perfect accuracy to not lose instantly.

This system takes a **Statistical AI** approach. We analyze how humans of different skill levels actually perform. If a move has a high win rate among humans but Stockfish dislikes it, our system will still highlight it as a "Success Choice" because it has proven effectiveness in practical play.

## 2. Bivariate Analysis: Rating vs. Success
The goodness of a chess move is relative to the skill of the players. We implement **Bivariate Analysis** by grouping data into four Elo-based buckets:
- **Novice (<1200)**: Tactical blunders are common; practical tricks are highly effective.
- **Intermediate (1200–1600)**: Club players where basic opening theory is established.
- **Advanced (1600–2000)**: Strong players familiar with theoretical middle games.
- **Expert/Master (2000+)**: Professional-level play where precision is significantly higher.

This allows the AI to provide context: *"Experts win with this 65% of the time, but it's rarely played by novices."*

## 3. Advanced Mathematical Logic

### Bayesian Smoothing
To handle "Rare Move" bias (moves with 100% win rate from a single game), we apply Bayesian Smoothing:
$$SmoothedWinRate = \frac{TotalWins + 5}{TotalGames + 10}$$
This "pulls" the win rate toward a 50% mean when sample size is low, ensuring only statistically significant moves reach the recommendations.

### Blended Confidence Score
We rank moves using a weighted multi-factor formula:
$$Score = (WinRate \times 0.5) + \left(\frac{AvgElo}{3000} \times 0.3\right) + (Popularity \times 0.2)$$
This ensures that **Most Popular** moves (mainline theory) naturally compete with **High Success** moves (practical gems) and **Expert Picks**.

### Blunder Guard
A hard **0.5% Popularity Floor** is enforced. Any move played by fewer than 0.5% of players in that position is rejected from general recommendations to protect the user from statistical noise or fluke wins.

## 4. Serving Model: Categorized Advice
Instead of a single "Best Move," the system serves three distinct strategic choices:
1. **Most Popular**: The consensus mainline choice.
2. **Highest Success**: The move with the best practical win rate (smoothed).
3. **Pro's Choice**: The move favored by players in the Expert bucket.
