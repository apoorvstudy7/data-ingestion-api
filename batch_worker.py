import threading
import time
import heapq
from store import batch_store, ingestion_store

# Priority mapping
PRIORITY_MAP = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}

# The job queue: (priority, created_time, ingestion_id, batch_id)
job_queue = []
queue_lock = threading.Lock()
worker_started = False
last_batch_time = 0  # Track when the last batch was processed

def enqueue_batches(ingestion_id, priority, batch_ids):
    global worker_started
    if priority not in PRIORITY_MAP:
        raise ValueError(f"Invalid priority: {priority}. Must be one of {list(PRIORITY_MAP.keys())}")
    
    with queue_lock:
        created_time = ingestion_store[ingestion_id]['created_time']
        for batch_id in batch_ids:
            heapq.heappush(job_queue, (PRIORITY_MAP[priority], created_time, ingestion_id, batch_id))
    if not worker_started:
        threading.Thread(target=batch_worker, daemon=True).start()
        worker_started = True

def batch_worker():
    global last_batch_time
    while True:
        with queue_lock:
            if not job_queue:
                time.sleep(1)
                continue
            priority, created_time, ingestion_id, batch_id = heapq.heappop(job_queue)
            batch = batch_store[batch_id]
            if batch['status'] != 'yet_to_start':
                continue
            batch['status'] = 'triggered'
        
        # Process the batch
        try:
            # Simulate external API call for each id in batch
            for _id in batch['ids']:
                time.sleep(1)  # Simulate delay per id
            
            # Update batch status
            batch['status'] = 'completed'
            
            # Enforce rate limiting: ensure at least 5 seconds between batches
            current_time = time.time()
            time_since_last_batch = current_time - last_batch_time
            if time_since_last_batch < 5:
                time.sleep(5 - time_since_last_batch)
            last_batch_time = time.time()
            
        except Exception as e:
            # If there's an error, mark the batch as failed
            batch['status'] = 'failed'
            batch['error'] = str(e) 