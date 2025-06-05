from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal
import uuid
import time
import logging
import webbrowser
import os
from store import ingestion_store, batch_store
from batch_worker import enqueue_batches

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if we're in production
IS_PRODUCTION = os.getenv('ENVIRONMENT') == 'production'

app = FastAPI(
    title="Data Ingestion API",
    description="API for asynchronous, rate-limited data ingestion with priority-based batch processing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not IS_PRODUCTION else [os.getenv('FRONTEND_URL', 'http://localhost:8000')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.on_event("startup")
async def startup_event():
    if not IS_PRODUCTION:
        # Only open browser in development
        frontend_url = 'http://localhost:8000'
        webbrowser.open(frontend_url)
        
        # Print startup message
        logger.info("\n" + "="*50)
        logger.info("🚀 Data Ingestion API is running!")
        logger.info(f"📝 API Documentation: {frontend_url}/docs")
        logger.info(f"🌐 Frontend: {frontend_url}")
        logger.info("="*50 + "\n")
    else:
        logger.info("🚀 Data Ingestion API is running in production mode")

class IngestRequest(BaseModel):
    ids: List[int] = Field(..., min_items=1)
    priority: Literal['HIGH', 'MEDIUM', 'LOW']

@app.post("/ingest")
def ingest(request: IngestRequest):
    logger.info(f"Received ingest request with ids: {request.ids}, priority: {request.priority}")
    ingestion_id = str(uuid.uuid4())
    ids = request.ids
    priority = request.priority
    # Split into batches of 3
    batches = [ids[i:i+3] for i in range(0, len(ids), 3)]
    batch_ids = []
    for batch in batches:
        batch_id = str(uuid.uuid4())
        batch_ids.append(batch_id)
        batch_store[batch_id] = {
            'ids': batch,
            'status': 'yet_to_start',
            'ingestion_id': ingestion_id
        }
    ingestion_store[ingestion_id] = {
        'priority': priority,
        'created_time': time.time(),  # Using proper timestamp
        'batch_ids': batch_ids
    }
    enqueue_batches(ingestion_id, priority, batch_ids)
    logger.info(f"Created ingestion with ID: {ingestion_id}")
    return {"ingestion_id": ingestion_id}

@app.get("/status/{ingestion_id}")
def status(ingestion_id: str):
    logger.info(f"Checking status for ingestion_id: {ingestion_id}")
    if ingestion_id not in ingestion_store:
        logger.warning(f"Ingestion ID not found: {ingestion_id}")
        raise HTTPException(status_code=404, detail="Ingestion ID not found")
    ingestion = ingestion_store[ingestion_id]
    batch_ids = ingestion['batch_ids']
    batches = []
    statuses = set()
    for batch_id in batch_ids:
        batch = batch_store[batch_id]
        batches.append({
            'batch_id': batch_id,
            'ids': batch['ids'],
            'status': batch['status']
        })
        statuses.add(batch['status'])
    if statuses == {'yet_to_start'}:
        overall_status = 'yet_to_start'
    elif statuses == {'completed'}:
        overall_status = 'completed'
    elif 'triggered' in statuses:
        overall_status = 'triggered'
    else:
        overall_status = 'yet_to_start'
    logger.info(f"Status for {ingestion_id}: {overall_status}")
    return {
        'ingestion_id': ingestion_id,
        'status': overall_status,
        'batches': batches
    } 