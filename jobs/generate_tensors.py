import os
import sys
import numpy as np
import chess
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, ArrayType, FloatType, IntegerType

# Configure Spark for local environment
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

def fen_to_tensor_and_label(row):
    """
    Transforms a FEN string into a 1D array representing a 12x8x8 tensor,
    and maps the UCI move to an integer index (0-4095).
    """
    fen = row.Position_FEN
    move_uci = row.Move_Played
    
    # 1. Map Move to 4096-Index
    # Handle promotions (e.g. e7e8q) by just ignoring the promotion piece for the index
    # (a simplified approach for this architecture)
    from_sq_str = move_uci[:2]
    to_sq_str = move_uci[2:4]
    
    try:
        from_sq = chess.parse_square(from_sq_str)
        to_sq = chess.parse_square(to_sq_str)
        move_index = from_sq * 64 + to_sq
    except ValueError:
        return None # Invalid square
        
    # 2. Map FEN to 12x8x8 Tensor (Flattened to 768)
    # Channels: 0-5 for White (P,N,B,R,Q,K), 6-11 for Black (p,n,b,r,q,k)
    board = chess.Board(fen)
    tensor = np.zeros((12, 8, 8), dtype=np.float32)
    
    piece_to_channel = {
        'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
        'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
    }
    
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            channel = piece_to_channel[piece.symbol()]
            # chess.SQUARES maps 0 to a1, 63 to h8.
            # Rank 0 is row 7 (bottom), File 0 is col 0 (left).
            row_idx = 7 - chess.square_rank(sq)
            col_idx = chess.square_file(sq)
            tensor[channel, row_idx, col_idx] = 1.0
            
    return (tensor.flatten().tolist(), int(move_index))

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("Chess_Tensor_Generator") \
        .master("local[*]") \
        .config("spark.driver.memory", "6g") \
        .config("spark.executor.memory", "6g") \
        .getOrCreate()
        
    print("Spark context initialized for Tensor Generation Phase.")
    
    input_path = "hdfs://localhost:9000/chess/exploded_positions.parquet"
    output_path = "hdfs://localhost:9000/chess/tensors.parquet"
    
    print(f"Reading positions from {input_path}...")
    df_positions = spark.read.parquet(input_path)
    
    # FILTER: Expert-Only Data (Elo >= 2000)
    print("Filtering for Expert-Only moves (Elo >= 2000)...")
    df_experts = df_positions.filter(df_positions.Player_Elo >= 2000)
    
    print(f"Expert positions found: {df_experts.count()}")
    
    # Process tensors
    print("Generating 12x8x8 Tensors... This is extremely computationally heavy.")
    
    # Use RDD to map Python logic
    tensors_rdd = df_experts.rdd.map(fen_to_tensor_and_label).filter(lambda x: x is not None)
    
    schema = StructType([
        StructField("board_tensor", ArrayType(FloatType()), False),
        StructField("target_move", IntegerType(), False)
    ])
    
    df_tensors = spark.createDataFrame(tensors_rdd, schema)
    
    # HDFS 128MB Block Alignment
    # A single row (768 floats + 1 int) is ~3KB. 
    # To get ~128MB partitions, we want ~40,000 rows per partition.
    # We will just specify a reasonable number of partitions for parallel training.
    # Since we don't know the exact count post-filter, we can repartition by an estimate.
    # For a robust approach, we save without repartition to let Spark handle it based on block size,
    # OR we explicitly repartition.
    
    print(f"Saving tensors to {output_path} in Parquet format...")
    df_tensors.write \
        .mode("overwrite") \
        .parquet(output_path)
        
    print("Tensor Generation completed successfully! Data is ready for PyTorch.")
    spark.stop()
