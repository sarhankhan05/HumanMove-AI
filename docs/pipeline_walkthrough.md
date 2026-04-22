# Pipeline Walkthrough: Hybrid Engine

This guide details the complete execution flow from raw PGN data to a live Hybrid AI interface.

## Step 1: Data Chunking & HDFS Ingestion
- Use `scripts/split_pgn.py` to chunk raw data into 128MB pieces.
- Upload to HDFS using `scripts/hdfs_upload.cmd`.

## Step 2: HDFS Optimization
- Ensure `hdfs-site.xml` is configured with `dfs.blocksize = 128MB` and `dfs.replication = 3`. This is crucial for Phase 4.

## Step 3: Distributed Parsing & Explosion
- **`jobs/parse_pgn.py`**: Filter and structure the PGN into Parquet.
- **`jobs/generate_positions.py`**: Expand games into ~29.2M board states (FENs).

## Step 4: Tensor Engineering (Data Prep for AI)
**File**: `jobs/generate_tensors.py`
- Converts FEN strings into $8 \times 8 \times 12$ numerical arrays.
- Filters for Expert-Only data (Elo >= 2000) to create a high-quality training set.
- Maps UCI moves to a 4096-dimensional output vector.
- **Output**: `hdfs:///chess/tensors.parquet`.

## Step 5: Data Sync (HDFS to Local)
- To avoid native HDFS library overhead during training, pull the tensors to the local disk:
  ```bash
  hdfs dfs -get /chess/tensors.parquet datasets/
  ```

## Step 6: Deep Learning (CNN Training)
**File**: `jobs/train_cnn.py`
- Trains a Convolutional Neural Network using **PyTorch**.
- Utilizes **CUDA** for GPU acceleration.
- **Output**: `models/chess_cnn.pth` (Serialized weights).

## Step 7: MongoDB Statistical Sync
- Run `jobs/build_recommendations.py` and `jobs/load_to_mongodb.py` to populate the historical win-rate database for the "Hybrid" context.

## Step 8: Hybrid Serving
**File**: `server/main.py`
- Launches a FastAPI server that performs **GPU Inference** on every request.
- Combines AI strategy with Big Data statistics and returns a hybridized JSON response.

## Step 9: Analytical Interface
- Serve the `/frontend` using a Python HTTP server.
- The UI displays the "Deep Learning AI" card alongside the "Statistical Edge" cards for an explainable strategic overview.
