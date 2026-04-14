import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType

# Configure Spark for local environment
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

def explode_game_to_positions(row):
    """
    FlatMap function to transform one game into multiple position rows.
    Input: Row(Position_FEN, White_Elo, Black_Elo, Result_Num, Move_List)
    """
    import chess
    
    # We use the starting FEN from the game row if available, otherwise default
    start_fen = row.Position_FEN if row.Position_FEN else chess.STARTING_FEN
    board = chess.Board(start_fen)
    moves = row.Move_List.split(" ")
    
    positions = []
    
    for move_uci in moves:
        if not move_uci:
            continue
            
        # Current state before the move
        # Stripped FEN: Piece Placement + Side to Move + Castling + En Passant
        # We ignore halfmove clock and fullmove number for better aggregation
        current_fen = " ".join(board.fen().split(" ")[:4])
        
        turn = board.turn # True for White, False for Black
        player_elo = row.White_Elo if turn == chess.WHITE else row.Black_Elo
        
        # Result from the perspective of the player whose turn it is
        if turn == chess.WHITE:
            player_result = row.Result_Num
        else:
            player_result = 1.0 - row.Result_Num
            
        # Add entry
        positions.append((
            current_fen,
            move_uci,
            player_elo,
            player_result
        ))
        
        # Apply the move to the board
        try:
            board.push_uci(move_uci)
        except Exception:
            # If a move is somehow invalid, stop processing this game
            break
            
    return positions

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("Chess_Position_Exploder") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()
        
    print("Spark context initialized for Data Explosion Phase.")
    
    input_path = "hdfs://localhost:9000/chess/processed_games.parquet"
    output_path = "hdfs://localhost:9000/chess/exploded_positions.parquet"
    
    print(f"Reading processed games from {input_path}...")
    df_games = spark.read.parquet(input_path)
    
    # Use RDD flatMap for the explosion logic as it's more flexible for custom chess-logic
    positions_rdd = df_games.rdd.flatMap(explode_game_to_positions)
    
    # Define schema for the exploded data
    schema = StructType([
        StructField("Position_FEN", StringType(), False),
        StructField("Move_Played", StringType(), False),
        StructField("Player_Elo", IntegerType(), True),
        StructField("Player_Result", FloatType(), False)
    ])
    
    print("Exploding games into positions... This may take a while.")
    df_positions = spark.createDataFrame(positions_rdd, schema)
    
    # Scale Management: Repartition to handle the large number of resulting rows (~20M+)
    # This prevents small files and helps with the next aggregation step.
    num_partitions = 32
    print(f"Repartitioning into {num_partitions} partitions and saving to {output_path}...")
    
    df_positions.repartition(num_partitions) \
        .write \
        .mode("overwrite") \
        .parquet(output_path)
        
    print("Phase 3 & 4 completed successfully!")
    
    # Quick sanity check
    count = spark.read.parquet(output_path).count()
    print(f"Total positions generated: {count}")
    
    spark.stop()
