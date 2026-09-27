"""
Kafka Producer - Website Event Simulator
========================================
This script generates realistic website events and sends them to Kafka
for testing the real-time pipeline.

Run: python data-engineering/kafka/producer.py
Purpose: Simulate user activity (page views, clicks, scrolls) on a website
"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

# ============================================================
# Kafka Connection Setup
# ============================================================

# Connect to Kafka broker running on localhost
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Convert dict to JSON bytes
)

# ============================================================
# Mock Data for Event Generation
# ============================================================

# Sample pages a user might visit
PAGES = [
    {'url': '/home', 'category': 'home'},
    {'url': '/products', 'category': 'products'},
    {'url': '/about', 'category': 'about'},
    {'url': '/blog', 'category': 'blog'},
    {'url': '/contact', 'category': 'contact'},
]

# Device types, browsers, and traffic sources
DEVICES = ['mobile', 'desktop', 'tablet']
BROWSERS = ['chrome', 'firefox', 'safari', 'edge']
SOURCES = ['google', 'direct', 'social', 'email', 'referral']

# ============================================================
# Event Generator
# ============================================================

def generate_event():
    """
    Generate a single realistic website event.
    
    Returns:
        dict: A complete event with user, session, page, and device details
    """
    return {
        # User and Session
        'user_id': f"user_{random.randint(1, 100)}",
        'session_id': f"sess_{random.randint(10000, 99999)}",
        
        # Page Information
        'page_url': random.choice(PAGES)['url'],
        'page_category': random.choice(PAGES)['category'],
        
        # Device and Browser
        'device_type': random.choice(DEVICES),
        'browser': random.choice(BROWSERS),
        'os': random.choice(['windows', 'macos', 'android', 'ios']),
        
        # Event Details
        'event_type': random.choice(['page_view', 'click', 'scroll']),
        'timestamp': datetime.now().isoformat(),
        
        # Performance Metrics
        'load_time_ms': random.randint(200, 3000),
        'time_on_page_seconds': random.randint(1, 120),
        'scroll_depth_pct': random.randint(20, 100),
        
        # Traffic Attribution
        'traffic_source': random.choice(SOURCES),
        'referrer_url': 'https://google.com/search?q=data+engineering',
        
        # Engagement Flags
        'is_bounce': random.random() < 0.30,      # 30% bounce rate
        'is_conversion': random.random() < 0.05,  # 5% conversion rate
        'conversion_value': round(random.uniform(10, 500), 2)
    }

# ============================================================
# Main Execution
# ============================================================

def main():
    """
    Main entry point for the Kafka producer.
    Sends events to the 'website_events' topic every 0.5-2 seconds.
    Press Ctrl+C to stop.
    """
    print("Starting Kafka Producer...")
    print("Sending events to topic: website_events")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Generate and send event
            event = generate_event()
            producer.send('website_events', value=event)
            print(f"Sent: {event['user_id']} | {event['page_url']} | {event['event_type']}")
            
            # Random delay to simulate real user activity
            time.sleep(random.uniform(0.5, 2.0))
            
    except KeyboardInterrupt:
        print("\nProducer stopped.")
        producer.close()

if __name__ == "__main__":
    main()