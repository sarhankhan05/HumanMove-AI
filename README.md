# Chess Move Recommendation System ♟️🤖

A high-performance Big Data & AI pipeline that analyzes millions of chess games to provide context-aware move recommendations based on historical human success rates, popularity, and player rating.

## 🚀 Project Overview
This project transforms raw PGN (Portable Game Notation) data into a real-time recommendation engine. Unlike traditional chess engines (like Stockfish) which focus on mathematical perfection, this system focuses on **Human Success Rates**. It answers the question: *"What do players at my level actually play, and what move wins the most often?"*

### 🛠️ Tech Stack
- **Storage**: HDFS (Pseudo-distributed)
- **Processing**: PySpark (Batch Processing)
- **Database**: MongoDB (Serving layer with Hashed Indexing)
- **API**: FastAPI (Uvicorn)
- **AI/ML**: Statistical Recommendation Engine with Bayesian Smoothing

## 🌟 Key Features
- **Bivariate Analysis**: Evaluates move success relative to player Elo ratings.
- **Bayesian Smoothing**: Pulls win rates toward a 50% mean to eliminate noise from low-sample "rare" moves.
- **Blunder Guard**: Filters out sub-optimal moves with less than 0.5% popularity.
- **Categorized Advice**: Provides three distinct recommendation types:
  - 👥 **Most Popular**: The consensus move played by the majority.
  - 🏆 **Highest Success**: The move with the best smoothed win rate.
  - 🎓 **Pro's Choice**: The move trusted most by Experts (2000+ Elo).

## 📂 Project Structure
- `/jobs`: PySpark batch jobs for PGN parsing, FEN explosion, and statistical modeling.
- `/server`: FastAPI backend for real-time serving.
- `/scripts`: Utility scripts for dataset management and HDFS uploads.
- `/docs`: Detailed architecture and pipeline documentation.

## 🏁 Quick Start
1. **Environment Setup**: `pip install -r requirements.txt`
2. **Data Preparation**: Run `scripts/split_pgn.py` to chunk the dataset for Spark.
3. **Data Pipeline**:
   - `python jobs/parse_pgn.py` (Parse PGN to Parquet)
   - `python jobs/generate_positions.py` (Explode to 29M+ FEN states)
   - `python jobs/build_recommendations.py` (Statistical Modeling)
   - `python jobs/load_to_mongodb.py` (Load to MongoDB)
4. **Serving**: `python -m uvicorn server.main:app`

## 📄 Documentation
For a deep dive into the architecture and the step-by-step pipeline, check out the [docs/](docs/) folder.
