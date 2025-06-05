# In-memory stores for ingestions and batches
# ingestion_store: {ingestion_id: {priority, created_time, batch_ids}}
ingestion_store = {}
# batch_store: {batch_id: {ids, status, ingestion_id}}
batch_store = {} 