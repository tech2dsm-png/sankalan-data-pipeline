"""
FastAPI - Receives events from website and sends to Kafka
Run: uvicorn data-engineering.api.app:app --reload --port 5000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from kafka import KafkaProducer
import json
from datetime import datetime
from typing import Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# Data Models
# ============================================================

class WebsiteEvent(BaseModel):
    user_id: str
    session_id: str
    page_url: str
    page_category: str
    device_type: str
    browser: str
    os: str
    event_type: str
    timestamp: Optional[str] = None
    load_time_ms: Optional[int] = None
    time_on_page_seconds: Optional[int] = None
    scroll_depth_pct: Optional[int] = None
    traffic_source: Optional[str] = None
    referrer_url: Optional[str] = None
    is_bounce: Optional[bool] = False
    is_conversion: Optional[bool] = False
    conversion_value: Optional[float] = 0.0
    
    # Add these extra fields that your tracking script sends
    element_text: Optional[str] = None
    element_href: Optional[str] = None
    element_id: Optional[str] = None
    element_class: Optional[str] = None
    form_id: Optional[str] = None
    form_action: Optional[str] = None
    form_method: Optional[str] = None
    form_fields: Optional[dict] = None
    test: Optional[bool] = False
    metadata: Optional[dict] = {}

# ============================================================
# Kafka Producer
# ============================================================

try:
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        retries=3,
        acks='all'  # Wait for all replicas to acknowledge
    )
    logger.info("✅ Kafka producer initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Kafka producer: {e}")
    producer = None

# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="Sankalan Event API",
    description="Receives website events and forwards to Kafka",
    version="1.0.0"
)

# ============================================================
# CORS Middleware
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.sankalandtech.com",
        "https://sankalandtech.com",
        "https://*.ngrok-free.app",  # Allow ngrok
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:8000",
        "*"  # For development - allows all origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
async def root():
    return {
        "service": "Sankalan Event API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "kafka_status": "connected" if producer else "disconnected"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "event-api",
        "kafka": "connected" if producer else "disconnected"
    }

@app.post("/event", status_code=201)
async def receive_event(event: WebsiteEvent):
    try:
        # Convert to dict
        event_data = event.dict()
        
        # Add timestamp if not provided
        if event_data.get('timestamp') is None:
            event_data['timestamp'] = datetime.now().isoformat()
        
        # Add received timestamp
        event_data['received_at'] = datetime.now().isoformat()
        
        logger.info(f"📥 Received event: {event.event_type} from user {event.user_id[:8]}...")
        
        # Send to Kafka
        if producer:
            future = producer.send('website_events', value=event_data)
            result = future.get(timeout=10)  # Wait for Kafka to acknowledge
            logger.info(f"✅ Event sent to Kafka: partition={result.partition}, offset={result.offset}")
        else:
            # If Kafka is not available, just log
            logger.warning("⚠️ Kafka not available, event logged only")
        
        return {
            "status": "success",
            "message": "Event sent to Kafka" if producer else "Event logged (Kafka unavailable)",
            "event_data": event_data
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to process event: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process event: {str(e)}"
        )

@app.post("/events", status_code=201)
async def receive_events(events: list[WebsiteEvent]):
    """
    Receive multiple events at once (for batching)
    """
    results = []
    for event in events:
        try:
            event_data = event.dict()
            if event_data.get('timestamp') is None:
                event_data['timestamp'] = datetime.now().isoformat()
            event_data['received_at'] = datetime.now().isoformat()
            
            if producer:
                producer.send('website_events', value=event_data)
            results.append({"user_id": event.user_id, "event_type": event.event_type, "status": "success"})
        except Exception as e:
            results.append({"user_id": event.user_id, "event_type": event.event_type, "status": "error", "error": str(e)})
    
    # Flush all messages
    if producer:
        producer.flush()
    
    return {
        "status": "success",
        "message": f"Processed {len(events)} events",
        "results": results
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Close Kafka producer on shutdown"""
    if producer:
        producer.close()
        logger.info("Kafka producer closed")

# ============================================================
# Run the app (for local testing)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 SANKALAN EVENT API")
    print("=" * 60)
    print(f"📡 Server: http://localhost:5000")
    print(f"📊 API Docs: http://localhost:5000/docs")
    print(f"🔍 Health: http://localhost:5000/health")
    print(f"📨 Kafka: {'✅ Connected' if producer else '❌ Disconnected'}")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=5000)