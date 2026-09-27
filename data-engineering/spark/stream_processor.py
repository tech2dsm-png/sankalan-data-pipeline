"""
Spark Streaming Processor - Production Ready
=============================================
Consumes events from Kafka using Spark's built-in Kafka connector,
applies watermarking for late data handling,
and writes processed data to PostgreSQL.

Run: spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 --conf spark.driver.host=localhost --conf spark.driver.bindAddress=127.0.0.1 --conf spark.sql.streaming.forceDeleteTempCheckpointLocation=true --conf spark.driver.extraJavaOptions="--add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED" --conf spark.executor.extraJavaOptions="--add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED" data-engineering/spark/stream_processor.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
# Remove this line: from pyspark.sql.streaming import Trigger

# ============================================================
# Spark Session Configuration
# ============================================================

spark = SparkSession.builder \
    .appName("SankalanRealTimePipeline") \
    .config("spark.driver.host", "localhost") \
    .config("spark.driver.bindAddress", "127.0.0.1") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .config("spark.sql.adaptive.enabled", "false") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# ============================================================
# Define JSON Schema for Incoming Events
# ============================================================

schema = StructType([
    StructField("user_id", StringType(), True),
    StructField("session_id", StringType(), True),
    StructField("page_url", StringType(), True),
    StructField("page_category", StringType(), True),
    StructField("device_type", StringType(), True),
    StructField("browser", StringType(), True),
    StructField("os", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("load_time_ms", IntegerType(), True),
    StructField("time_on_page_seconds", IntegerType(), True),
    StructField("scroll_depth_pct", IntegerType(), True),
    StructField("traffic_source", StringType(), True),
    StructField("referrer_url", StringType(), True),
    StructField("is_bounce", BooleanType(), True),
    StructField("is_conversion", BooleanType(), True),
    StructField("conversion_value", DoubleType(), True)
])

# ============================================================
# Read Streaming Data from Kafka
# ============================================================

df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "website_events") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# Parse JSON and apply schema
df_parsed = df_raw.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# Convert timestamp string to Spark timestamp type
df_events = df_parsed.withColumn("event_timestamp", to_timestamp(col("timestamp")))

# ============================================================
# Watermarking - Handle Late-Arriving Data
# ============================================================

df_events = df_events.withWatermark("event_timestamp", "5 minutes")

# ============================================================
# Write to PostgreSQL - FIXED VERSION
# ============================================================

def write_to_postgres(df, epoch_id):
    """
    Write each micro-batch to PostgreSQL fact table.
    """
    if df.isEmpty():
        return
    
    # FIX: Removed 'analytics.' from dbtable and added currentSchema
    jdbc_url = "jdbc:postgresql://localhost:5432/analytics?currentSchema=public"
    
    # FIX: Added 'stringtype=unspecified' to handle timezone issues
    jdbc_props = {
        "user": "sankalan",
        "password": "sankalan123",
        "driver": "org.postgresql.Driver",
        "batchsize": "1000",
        "stringtype": "unspecified"
    }
    
    # Select only columns that match the fact table schema
    df_fact = df.select(
        "session_id", "user_id", "page_url", "device_type",
        "event_timestamp", "event_type", "load_time_ms",
        "time_on_page_seconds", "scroll_depth_pct",
        "traffic_source", "referrer_url",
        "is_bounce", "is_conversion", "conversion_value"
    )
    
    # Write to fact_page_views table (without schema prefix)
    df_fact.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "fact_page_views") \
        .options(**jdbc_props) \
        .mode("append") \
        .save()
    
    print(f"Batch {epoch_id}: {df.count()} events written to PostgreSQL")

# ============================================================
# Start Streaming Query
# ============================================================

# FIX: Removed Trigger.ProcessingTime and used processingTime directly
query = df_events.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("append") \
    .trigger(processingTime="10 seconds") \
    .option("checkpointLocation", "checkpoints/spark-streaming") \
    .start()

print("=" * 60)
print("Spark Streaming Started")
print("=" * 60)
print("Application: SankalanRealTimePipeline")
print("Kafka Topic: website_events")
print("PostgreSQL: fact_page_views")
print("Checkpoint: checkpoints/spark-streaming")
print("Trigger: 10 seconds")
print("=" * 60)
print("Waiting for data... Press Ctrl+C to stop")
print("=" * 60)

query.awaitTermination()