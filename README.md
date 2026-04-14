# Chess Move Recommendation System ♟️🤖

A high-performance Big Data & AI pipeline that analyzes millions of chess positions using PySpark on HDFS to provide real-time, context-aware strategic advice.

## 🚀 Project Overview
This project transforms raw PGN (Portable Game Notation) data into a professional-grade analytical tool. Unlike traditional engines that seek mathematical perfection, this system uses **Human Success Rates** and **Bivariate Analysis** to recommend moves that win in practical play for specific rating levels.

### 🛠️ Tech Stack
- **Storage**: HDFS (Pseudo-distributed)
- **Processing**: PySpark (Distributed Batch Modeling)
- **Database**: MongoDB (Serving layer with Hashed Indexing)
- **API**: FastAPI (Low-latency Serving)
- **Frontend**: Vanilla JS + Chessboard.js (Futuristic Analytical UI)

## 🌟 Key Features
- **Categorized AI Selection**:
  - 👥 **The Standard Path**: The consensus most popular move.
  - 🏆 **The Statistical Edge**: The move with the highest Bayesian-smoothed win rate.
  - 🎓 **The Master's Secret**: The move trusted by Expert/Master players (2000+ Elo).
- **Bayesian Smoothing**: Eliminates "Rare Move" bias by pulling infrequent data toward a 50% mean.
- **Blended Confidence Score**: Ranks moves by weighing Success (50%), Player Elo (30%), and Popularity (20%).
- **Blunder Guard**: Automatically filters out moves with less than 0.5% popularity to ensure strategic reliability.
- **Futuristic UI**: A Slate/Blue "Cyber Gray" dashboard with real-time analysis and glassmorphic cards.

## 📂 Project Structure
- `/jobs`: PySpark batch jobs for PGN parsing, FEN explosion, and statistical modeling.
- `/server`: FastAPI backend for real-time serving.
- `/frontend`: Interactive UI with local high-contrast piece assets.
- `/docs`: Detailed architecture and pipeline documentation.

## 🏁 Quick Start
1. **Environment Setup**: `pip install -r requirements.txt`
2. **Data Pipeline**:
   - `python jobs/parse_pgn.py` (Parse PGN to Parquet)
   - `python jobs/generate_positions.py` (Explode to 29.2M FEN states)
   - `python jobs/build_recommendations.py` (Statistical Modeling)
   - `python jobs/load_to_mongodb.py` (Load to MongoDB)
3. **Serving (Backend)**: 
   ```bash
   python -m uvicorn server.main:app
   ```
4. **UI (Frontend)**:
   ```bash
   cd frontend
   python -m http.server 5173
   ```

## 📄 Documentation
- [Architecture & AI Philosophy](docs/architecture.md)
- [Step-by-Step Pipeline Walkthrough](docs/pipeline_walkthrough.md)
