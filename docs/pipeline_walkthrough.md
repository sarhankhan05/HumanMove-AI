# Pipeline Walkthrough

This document serves as a step-by-step guide for developers to execute the data pipeline from raw PGN data to a live API and UI.

## Step 1: Data Chunking
**File**: `scripts/split_pgn.py`
- Splits large `.pgn.zst` files into ~128MB chunks for Spark parallelism.
- **Output**: `datasets/chunks/*.pgn`.

## Step 2: HDFS Ingestion
**File**: `scripts/hdfs_upload.cmd`
- Uploads raw chunks to HDFS storage.
- **Output**: `hdfs://localhost:9000/chess/input/`.

## Step 3: Distributed Parsing
**File**: `jobs/parse_pgn.py`
- Distributed parsing using PySpark and `chess.pgn`.
- Filters for standard games and player Elo >= 1500.
- **Output**: `hdfs://localhost:9000/chess/processed_games.parquet`.

## Step 4: Position Explosion (FEN Generation)
**File**: `jobs/generate_positions.py`
- Explodes ~400k games into ~29.2M individual FEN board states.
- **Output**: `hdfs://localhost:9000/chess/exploded_positions.parquet`.

## Step 5: Statistical AI Modeling
**File**: `jobs/build_recommendations.py`
- Calculates Win Rates, Popularity, and Blended Confidence scores.
- Applies **Bayesian Smoothing** and **Blunder Guard** filters.
- **Output**: `hdfs://localhost:9000/chess/move_stats.parquet`.

## Step 6: MongoDB Serving Layer
**File**: `jobs/load_to_mongodb.py`
- Selects the **Categorized Top 3** (Most Popular, Success, Expert).
- Nests recommendations into a single document per FEN with a Hashed Index.
- **Output**: `chess_db.recommendations` collection.

## Step 7: API Serving
**File**: `server/main.py`
- FastAPI server providing the `/recommend` endpoint with sub-50ms latency.
- Configured with CORS for the frontend.

## Step 8: Interactive Frontend UI
**Directory**: `/frontend`
- A futuristic "Cyber Gray" dashboard built with Vanilla HTML/CSS/JS.
- **Move Logic**: Uses `chess.js` and `chessboard.js`.
- **Local Assets**: All chess pieces are hosted locally in `frontend/img/` to ensure 100% reliability and offline availability.
- **Launch**: Run `python -m http.server 5173` inside the `/frontend` directory.
