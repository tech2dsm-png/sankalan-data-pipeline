from kafka import KafkaConsumer
import json

print("Starting simple consumer...")
consumer = KafkaConsumer(
    'website_events',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='simple-test',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("Connected! Waiting for message...")
for msg in consumer:
    print(f"Received: {msg.value}")
    break

consumer.close()
print("Done!")