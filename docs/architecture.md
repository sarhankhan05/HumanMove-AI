# Project Architecture & AI Philosophy

This document explains the design decisions and mathematical logic behind the Chess Move Recommendation System.

## 1. The Core Philosophy: Human Success > Engine Perfection
Traditional chess engines like Stockfish are "Black Box" models designed for mathematical perfection. However, for a human player, Stockfish's top recommendation might be a line that requires 20 moves of perfect accuracy to not lose instantly.

This system takes a **Statistical AI** approach. We analyze how humans of different skill levels actually perform. If a move has a 60% win rate among humans but Stockfish hates it, our system will still recommend it as a "Success Choice" because it has proven effectiveness in practical play.

## 2. Bivariate Analysis: Rating vs. Success
The goodness of a chess move is relative to the skill of the players. We implement **Bivariate Analysis** by grouping data into four Elo-based buckets:
- **Novice (<1200)**: Casual play where tactical blunders are common.
- **Intermediate (1200–1600)**: Club players where basic theory is known.
- **Advanced (1600–2000)**: Strong players familiar with deep opening lines.
- **Expert/Master (2000+)**: Competitive tournament play.

This allows the AI to provide context: *"This move works great at 1400, but experts rarely play it because it's strategically risky."*

## 3. Bayesian Smoothing: Eliminating the "Rare Move" Bias
A major challenge in Big Data is handling data points with low support. A move played only once and won by luck would traditionally have a 100% win rate.

We apply **Bayesian Smoothing** to all win rates:
$$SmoothedWinRate = \frac{TotalWins + 5}{TotalGames + 10}$$
This formula "pulls" the win rate toward 50% when the sample size is small. As a move gains hundreds of observations, the raw data begins to dominate the smoothed score, ensuring only statistically significant trends reach theTop 3.

## 4. Serving Layer: MongoDB Nested Documents
To ensure the API handles requests in milliseconds, we use a **Single-Document-Per-FEN** structure in MongoDB.
- **Hashed Index**: We use a hashed index on the FEN string for $O(1)$ search complexity.
- **Nested Recommendations**: By nesting the Popular, Success, and Expert choices in one document, we avoid multiple database joins or queries, providing an ultra-responsive experience for the frontend.
