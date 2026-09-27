"""
Spark Streaming Processor - Using Kafka Python Consumer with Pandas
====================================================================
Consumes events from Kafka using kafka-python, processes them in batches using Pandas,
and writes processed data to PostgreSQL in Star Schema format.

Run: spark-submit --jars jars/postgresql-42.5.4.jar data-engineering/spark/stream_processor_kafka.py
"""

from kafka import KafkaConsumer
import json
import time
from datetime import datetime
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# ============================================================
# Spark Session Configuration
# ============================================================

spark = SparkSession.builder \
    .appName("SankalanRealTimePipeline") \
    .config("spark.driver.host", "localhost") \
    .config("spark.driver.bindAddress", "127.0.0.1") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .config("spark.sql.adaptive.enabled", "false") \
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

def write_to_postgres(df, batch_id):
    """Write DataFrame to PostgreSQL."""
    if df.isEmpty():
        return
    
    jdbc_url = "jdbc:postgresql://localhost:5432/analytics"
    jdbc_props = {
        "user": "sankalan",
        "password": "sankalan123",
        "driver": "org.postgresql.Driver"
    }
    
    df_fact = df.select(
        "session_id", "user_id", "page_url", "device_type",
        "event_timestamp", "event_type", "load_time_ms",
        "time_on_page_seconds", "scroll_depth_pct",
        "traffic_source", "referrer_url",
        "is_bounce", "is_conversion", "conversion_value"
    )
    
    df_fact.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "analytics.fact_page_views") \
        .options(**jdbc_props) \
        .mode("append") \
        .save()
    
    print(f"Batch {batch_id}: {df.count()} events written to PostgreSQL")

def process_messages():
    """Consume messages from Kafka and process them in batches."""
    
    print("=" * 60)
    print("Spark Streaming Processor - Real-time Data Pipeline")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Connecting to Kafka: localhost:9092")
    print("Topic: website_events")
    print("=" * 60)
    
    try:
        consumer = KafkaConsumer(
            'website_events',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='spark-processor-v6',
            max_poll_records=100,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print("Connected to Kafka successfully!")
        print("Listening for real-time messages...")
        print("Press Ctrl+C to stop.")
        print("=" * 60)
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return
    
    batch_size = 10
    messages = []
    batch_count = 0
    total_messages = 0
    start_time = time.time()
    
    try:
        for msg in consumer:
            data = msg.value
            messages.append(data)
            total_messages += 1
            
            if len(messages) >= batch_size:
                batch_count += 1
                elapsed = time.time() - start_time
                print(f"\n{'='*60}")
                print(f"Processing Batch #{batch_count}")
                print(f"Messages: {len(messages)}")
                print(f"Total messages so far: {total_messages}")
                print(f"Runtime: {elapsed:.2f} seconds")
                print(f"{'='*60}")
                
                try:
                    # Convert to pandas DataFrame first (serialization safe)
                    pdf = pd.DataFrame(messages)
                    
                    # Convert pandas to Spark DataFrame
                    df = spark.createDataFrame(pdf, schema)
                    df_events = df.withColumn("event_timestamp", to_timestamp(col("timestamp")))
                    df_events = df_events.withWatermark("event_timestamp", "5 minutes")
                    
                    # Show sample
                    print("\nSample data:")
                    df_events.select("user_id", "event_type", "page_url", "event_timestamp").show(5, truncate=False)
                    
                    write_to_postgres(df_events, batch_count)
                    messages = []
                    print(f"Batch {batch_count} completed successfully!")
                    print("=" * 60)
                    
                except Exception as e:
                    print(f"Error processing batch {batch_count}: {e}")
                    import traceback
                    traceback.print_exc()
                    messages = []  # Clear messages to avoid infinite loop
                
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Stopping consumer...")
        if messages:
            batch_count += 1
            print(f"Processing final batch {batch_count} with {len(messages)} messages...")
            try:
                pdf = pd.DataFrame(messages)
                df = spark.createDataFrame(pdf, schema)
                df_events = df.withColumn("event_timestamp", to_timestamp(col("timestamp")))
                df_events = df_events.withWatermark("event_timestamp", "5 minutes")
                write_to_postgres(df_events, batch_count)
            except Exception as e:
                print(f"Error processing final batch: {e}")
        consumer.close()
        print(f"Total messages processed: {total_messages}")
        print(f"Total runtime: {time.time() - start_time:.2f} seconds")
        print("Consumer stopped.")
        print("=" * 60)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        consumer.close()

if __name__ == "__main__":
    process_messages()