import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pymongo import MongoClient, UpdateOne

# Configure Spark
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

def load_partition_to_mongo(partition):
    client = MongoClient("mongodb://localhost:27017/")
    db = client["chess_db"]
    collection = db["recommendations"]
    
    batch = []
    batch_size = 500
    
    def format_move(row):
        if row is None or row.Move_Played is None:
            return None
        return {
            "move": row.Move_Played,
            "win_rate": float(row.Win_Probability),
            "popularity": row.Popularity_Str,
            "avg_elo": int(row.Avg_Elo),
            "confidence_score": float(row.Weighted_Confidence),
            "explanation": row.Explanation
        }

    for row in partition:
        # Construct document
        doc = {
            "_id": row.Position_FEN,
            "total_samples": row.Total_Samples,
            "recommendations": {
                "most_popular": format_move(row.popular_choice),
                "highest_success": format_move(row.success_choice),
                "pro_choice": format_move(row.expert_choice)
            }
        }
        batch.append(UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True))
        
        if len(batch) >= batch_size:
            collection.bulk_write(batch)
            batch = []
    
    if batch:
        collection.bulk_write(batch)
    client.close()

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("Chess_MongoDB_Categorizer") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()
        
    print("Spark initialized for Categorized MongoDB Loading.")
    
    input_path = "hdfs://localhost:9000/chess/move_stats.parquet"
    df = spark.read.parquet(input_path)
    
    # Identify Categories using Window Functions
    window_pop = Window.partitionBy("Position_FEN").orderBy(F.desc("Popularity_Dec"))
    window_success = Window.partitionBy("Position_FEN").orderBy(F.desc("Win_Probability"))
    window_expert = Window.partitionBy("Position_FEN").orderBy(F.desc("Expert_WP"))
    
    # 1. Most Popular
    pop_df = df.withColumn("rn", F.row_number().over(window_pop)) \
               .filter(F.col("rn") == 1) \
               .select("Position_FEN", F.struct("*").alias("popular_choice"))
               
    # 2. Highest Success (Min 1% popularity to avoid weird wins)
    success_df = df.filter(F.col("Popularity_Dec") >= 0.01) \
                   .withColumn("rn", F.row_number().over(window_success)) \
                   .filter(F.col("rn") == 1) \
                   .select("Position_FEN", F.struct("*").alias("success_choice"))
                   
    # 3. Pro's Choice (Must have expert data)
    expert_df = df.filter(F.col("Expert_WP").isNotNull()) \
                  .withColumn("rn", F.row_number().over(window_expert)) \
                  .filter(F.col("rn") == 1) \
                  .select("Position_FEN", F.struct("*").alias("expert_choice"))
                  
    # Join them all together
    final_df = df.select("Position_FEN", "Total_Samples").distinct() \
                 .join(pop_df, "Position_FEN", "left") \
                 .join(success_df, "Position_FEN", "left") \
                 .join(expert_df, "Position_FEN", "left")
    
    print("Loading categorized documents into MongoDB...")
    final_df.foreachPartition(load_partition_to_mongo)
    
    client = MongoClient("mongodb://localhost:27017/")
    client["chess_db"]["recommendations"].create_index([("_id", "hashed")])
    client.close()
    
    print("MongoDB Fresh Load Complete!")
    spark.stop()
