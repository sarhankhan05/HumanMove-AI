import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Configure Spark
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("Chess_Categorized_AI") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()
        
    print("Spark initialized for Categorized Recommendation Aggregation.")
    
    input_path = "hdfs://localhost:9000/chess/exploded_positions.parquet"
    output_path = "hdfs://localhost:9000/chess/move_stats.parquet"
    
    print(f"Reading exploded positions from {input_path}...")
    df = spark.read.parquet(input_path)
    
    # 1. Add Rating Buckets (Expert/Pro Threshold: 2000+)
    df = df.withColumn("Rating_Bucket", 
        F.when(F.col("Player_Elo") < 1200, "Novice")
         .when(F.col("Player_Elo") < 1600, "Intermediate")
         .when(F.col("Player_Elo") < 2000, "Advanced")
         .otherwise("Expert")
    )
    
    # 2. Bayesian Smoothing Aggregation
    print("Aggregating with Bayesian Smoothing and Weighted Confidence...")
    stats_df = df.groupBy("Position_FEN", "Move_Played").agg(
        F.count("Player_Result").alias("Frequency"),
        F.avg("Player_Elo").alias("Avg_Elo"),
        F.sum("Player_Result").alias("Total_Wins"),
        F.sum(F.when(F.col("Rating_Bucket") == "Expert", F.col("Player_Result"))).alias("Expert_Wins"),
        F.count(F.when(F.col("Rating_Bucket") == "Expert", True)).alias("Expert_Games")
    )
    
    # Position-level total count for Popularity calculation
    position_totals = df.groupBy("Position_FEN").agg(F.count("*").alias("Total_Samples"))
    stats_df = stats_df.join(position_totals, "Position_FEN")
    
    # Calculate Metrics
    stats_df = stats_df.withColumn(
        "Win_Probability",
        (F.col("Total_Wins") + 5.0) / (F.col("Frequency") + 10.0)
    ).withColumn(
        "Expert_WP",
        F.when(F.col("Expert_Games") >= 10, 
               (F.col("Expert_Wins") + 5.0) / (F.col("Expert_Games") + 10.0))
         .otherwise(F.lit(None))
    ).withColumn(
        "Popularity_Dec",
        F.col("Frequency") / F.col("Total_Samples")
    )
    
    # 3. New Weighting Formula (Blended Confidence)
    # Confidence = (WinRate * 0.5) + (AvgElo/3000 * 0.3) + (Popularity * 0.2)
    stats_df = stats_df.withColumn(
        "Weighted_Confidence",
        (F.col("Win_Probability") * 0.5) + ((F.col("Avg_Elo") / 3000.0) * 0.3) + (F.col("Popularity_Dec") * 0.2)
    )
    
    # 4. Apply Blunder Guard (Hard Popularity Floor at 0.5%)
    # For a move to be considered "General Advice", it must have >= 0.5% popularity
    print("Applying Blunder Guard (0.5% Popularity Floor)...")
    stats_df = stats_df.filter(F.col("Popularity_Dec") >= 0.005)
    
    # 5. Generate Explanation Text
    explanation_logic = F.concat(
        F.lit("Based on "), F.col("Frequency").cast("string"), F.lit(" games, this move has a "),
        F.round(F.col("Win_Probability") * 100, 1).cast("string"), F.lit("% global success rate. "),
        F.when(F.col("Expert_WP").isNotNull(),
               F.concat(F.lit("Experts win with this "), F.round(F.col("Expert_WP") * 100, 1).cast("string"), F.lit("% of the time."))
        ).otherwise(F.lit("Limited data at expert levels."))
    )
    stats_df = stats_df.withColumn("Explanation", explanation_logic)
    
    # Convert popularity to string for UI
    stats_df = stats_df.withColumn("Popularity_Str", F.concat(F.round(F.col("Popularity_Dec") * 100, 1).cast("string"), F.lit("%")))
    
    print(f"Saving categorized move statistics to {output_path}...")
    stats_df.write.mode("overwrite").parquet(output_path)
    
    print("Aggregation complete. Sample output for Starting Position:")
    stats_df.filter(F.col("Position_FEN").contains("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")) \
        .orderBy(F.desc("Weighted_Confidence")) \
        .select("Move_Played", "Popularity_Str", "Win_Probability", "Weighted_Confidence") \
        .show(10)
        
    spark.stop()
