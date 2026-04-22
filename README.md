# Hybrid Chess Move Recommendation System ♟️🤖

A high-performance Big Data & Deep Learning pipeline that analyzes millions of chess positions using PySpark on HDFS and a Convolutional Neural Network (CNN) to provide real-time, explainable strategic advice.

## 🚀 Project Overview
This project transforms raw PGN (Portable Game Notation) data into a professional-grade analytical tool. By combining **Big Data Statistics** (Human Success Rates) with **Deep Learning** (Strategic Pattern Recognition), the system provides a "Hybrid" recommendation that balances practical winning chances with theoretical master-level intent.

### 🛠️ Tech Stack
- **Storage**: HDFS (Optimized 128MB block sizing, Replication 3)
- **Processing**: PySpark (Distributed Tensor Generation)
- **AI**: PyTorch (CNN with 12-channel board representation + CUDA acceleration)
- **Database**: MongoDB (Serving layer for historical success stats)
- **API**: FastAPI (Hybrid Inference layer with Legal Move Masking)
- **Frontend**: Vanilla JS (Futuristic Slate/Blue Analytical UI)

## 🌟 Key Features
- **Hybrid AI Logic**:
  - 🧠 **Deep Learning AI**: A CNN trained on 2.2M+ expert positions (Elo > 2000) to recognize strategic patterns.
  - 📊 **Statistical Insights**: Real-time lookup of "Most Popular," "Highest Success," and "Master's Secret" from Big Data.
- **Explainable Predictions**: The UI combines the CNN's confidence percentage with historical human win rates.
- **Hadoop Optimization**: Configured HDFS for maximum Spark parallelism and Data Locality.
- **Legal Move Masking**: The FastAPI layer applies an algorithmic mask to the CNN's output to ensure 100% tactical legality.

## 📂 Project Structure
- `/jobs`: PySpark batch jobs (PGN parsing, Tensor generation) and PyTorch training.
- `/server`: Hybrid FastAPI backend.
- `/frontend`: Interactive dashboard.
- `/docs`: Detailed architecture and Hadoop optimization guides.

## 🏁 Quick Start
1. **Environment Setup**: `pip install -r requirements.txt`
2. **Data Pipeline**:
   - `python jobs/parse_pgn.py` (Parse PGN to Parquet)
   - `python jobs/generate_positions.py` (Explode to FEN states)
   - **New: `python jobs/generate_tensors.py`** (Generate 12x8x8 tensors)
3. **Training**:
   - `hdfs dfs -get /chess/tensors.parquet datasets/`
   - **New: `python jobs/train_cnn.py`** (Train PyTorch CNN on GPU)
4. **Serving**: 
   - `python -m uvicorn server.main:app` (Hybrid API)
   - `cd frontend && python -m http.server 5173` (Analytical UI)

## 📄 Documentation
- [Hybrid Architecture Philosophy](docs/architecture.md)
- [Hadoop Optimization Guide](docs/hadoop_optimization.md)
- [Pipeline Walkthrough](docs/pipeline_walkthrough.md)
