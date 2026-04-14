import os
import sys
# Configure Spark to use the virtual environment's Python
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType
import io

def parse_pgn_partition(records):
    """
    Function mapping over wholeTextFiles.
    records is an iterator of tuples: (file_path, file_content_string)
    """
    import chess.pgn
    import traceback
    
    for file_path, file_bytes in records:
        print(f"Beginning processing of {file_path}")
        byte_stream = io.BytesIO(file_bytes)
        text_stream = io.TextIOWrapper(byte_stream, encoding='utf-8')
        
        while True:
            try:
                game = chess.pgn.read_game(text_stream)
                if game is None:
                    break
                    
                # Data cleaning
                variant = game.headers.get("Variant", "Standard")
                if variant != "Standard":
                    continue
                    
                white_elo_str = game.headers.get("WhiteElo", "?")
                black_elo_str = game.headers.get("BlackElo", "?")
                
                try:
                    white_elo = int(white_elo_str)
                    black_elo = int(black_elo_str)
                except ValueError:
                    continue # Skip if elo is missing or malformed
                    
                if white_elo < 1500 or black_elo < 1500:
                    continue
                    
                # Collect moves
                moves = list(game.mainline_moves())
                if len(moves) < 10:
                    continue
                    
                move_list_str = " ".join([move.uci() for move in moves])
                
                # Result logic mapping (1 for white win, 0 for loss, 0.5 for draw)
                result_str = game.headers.get("Result", "*")
                if result_str == "1-0":
                    game_result = 1.0
                elif result_str == "0-1":
                    game_result = 0.0
                elif result_str == "1/2-1/2":
                    game_result = 0.5
                else:
                    continue # Ignore indeterminate results (*)
                    
                yield {
                    "Position_FEN": game.board().fen(), # Starting FEN
                    "White_Elo": white_elo,
                    "Black_Elo": black_elo,
                    "Result_Num": game_result,
                    "Result_Str": result_str,
                    "ECO": game.headers.get("ECO", "???"),
                    "Move_List": move_list_str
                }
            except Exception as e:
                # Catch malformed games inline and continue
                continue

if __name__ == "__main__":
    # Initialize Spark Session tailored for Max CPU utilization on the Host Laptop local[*]
    # and configuring memory boundaries to protect driving capabilities.
    spark = SparkSession.builder \
        .appName("Chess_PGN_Processor") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .config("spark.network.timeout", "800s") \
        .config("spark.executor.heartbeatInterval", "60s") \
        .getOrCreate()
        
    sc = spark.sparkContext
    sc.setLogLevel("WARN")
    
    print("Spark initialized. Local[*] mode with cores optimized for mapping.")
    print("Reading text files from hdfs://localhost:9000/chess/input/*.pgn ...")
    
    # Use binaryFiles to prevent Java String OutOfMemory errors and keep O(1) buffer logic
    raw_rdd = sc.binaryFiles("hdfs://localhost:9000/chess/input/*.pgn", minPartitions=16)
    
    # Apply MapPartitions utilizing chess.pgn parser natively
    parsed_rdd = raw_rdd.mapPartitions(parse_pgn_partition)
    
    # Explicit definition of DataFrame Schema
    schema = StructType([
        StructField("Position_FEN", StringType(), False),
        StructField("White_Elo", IntegerType(), True),
        StructField("Black_Elo", IntegerType(), True),
        StructField("Result_Num", FloatType(), False),
        StructField("Result_Str", StringType(), True),
        StructField("ECO", StringType(), True),
        StructField("Move_List", StringType(), False)
    ])
    
    df = spark.createDataFrame(parsed_rdd, schema)
    
    # Optional Repartition: This is highly recommended for writing normalized chunk sizes 
    # to Parquet as our data drops massive volume during < 1500 Elo filtering.
    output_partitions = 8
    print(f"Dataframe logic compiled. Saving to parquet format over {output_partitions} partitions...")
    
    output_path = "hdfs://localhost:9000/chess/processed_games.parquet"
    df.repartition(output_partitions) \
      .write \
      .mode("overwrite") \
      .parquet(output_path)
      
    print(f"Extraction and persistence to {output_path} successful!")
    
    # Simple sanity check
    df_loaded = spark.read.parquet(output_path)
    print(f"Total valid standard games successfully parsed: {df_loaded.count()}")
    
    spark.stop()
