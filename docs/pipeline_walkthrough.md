# Pipeline Walkthrough

This document serves as a step-by-step guide for developers to execute the data pipeline from raw PGN data to a live API.

## Step 1: Data Chunking
**File**: `scripts/split_pgn.py`
- **What it does**: Decompresses the `.pgn.zst` file and splits it into ~128MB PGN chunks.
- **Why**: PySpark's parallelism depends on having multiple files to distribute among workers. Splitting at game boundaries (`[Event ...`) ensures data integrity.
- **Output**: Multiple `.pgn` files in `datasets/chunks/`.
- **Verify**: Check the folder for `chunk_001.pgn`, `chunk_002.pgn`, etc.

## Step 2: HDFS Ingestion
**File**: `scripts/hdfs_upload.cmd`
- **What it does**: Creates the HDFS directory structure and uploads the chunks to the HDFS master.
- **Output**: Files stored in `hdfs://localhost:9000/chess/input/`.
- **Verify**: Run `hdfs dfs -ls /chess/input/` to see the uploaded chunks.

## Step 3: Distributed Parsing
**File**: `jobs/parse_pgn.py`
- **What it does**: A PySpark job that reads binary PGN files from HDFS and uses `mapPartitions` to parse them into a structured Spark DataFrame. It filters for games with standard variants, counts moves, and ensures player Elo >= 1500.
- **Output**: `hdfs://localhost:9000/chess/processed_games.parquet`.
- **Verify**: Check Spark logs for the total count of valid games parsed (~400k for the sample).

## Step 4: Position Explosion (FEN Generation)
**File**: `jobs/generate_positions.py`
- **What it does**: This is the most CPU-intensive step. It replays every move in the parsed games to generate the **FEN (Forsyth-Edwards Notation)** for every board state.
- **Output**: `hdfs://localhost:9000/chess/exploded_positions.parquet` (containing 20M–30M rows).
- **Verify**: Verify the row count in the Spark logs.

## Step 5: Statistical AI Modeling
**File**: `jobs/build_recommendations.py`
- **What it does**: Aggregates the exploded data to calculate win rates, popularity, and average Elo per move. It applies **Bayesian Smoothing**, the **Blended Confidence Formula**, and the **Blunder Guard** filter.
- **Output**: `hdfs://localhost:9000/chess/move_stats.parquet`.
- **Verify**: Check the sample console output for the "Starting Position" recommendations.

## Step 6: MongoDB Serving Layer
**File**: `jobs/load_to_mongodb.py`
- **What it does**: Selects the Top 3 categorical recommendations (Popular, Success, Expert) and nests them into a single record per FEN. Performs bulk upserts into MongoDB.
- **Output**: `chess_db.recommendations` collection.
- **Verify**: Use `mongosh` to find a record: `db.recommendations.findOne()`.

## Step 7: API Serving
**File**: `server/main.py`
- **What it does**: A FastAPI server that queries MongoDB using the hashed FEN index and returns recommendations in under 50ms.
- **Verify**: Navigate to `http://localhost:8000/recommend?fen=...` in your browser.
