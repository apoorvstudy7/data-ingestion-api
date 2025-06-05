import pytest
from httpx import AsyncClient
from main import app
import asyncio

@pytest.mark.asyncio
async def test_ingest_and_status():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Ingest MEDIUM priority
        resp1 = await ac.post("/ingest", json={"ids": [1,2,3,4,5], "priority": "MEDIUM"})
        assert resp1.status_code == 200
        ingestion_id1 = resp1.json()["ingestion_id"]

        # Wait 1s, then ingest HIGH priority
        await asyncio.sleep(1)
        resp2 = await ac.post("/ingest", json={"ids": [6,7,8,9], "priority": "HIGH"})
        assert resp2.status_code == 200
        ingestion_id2 = resp2.json()["ingestion_id"]

        # Wait for batches to process
        await asyncio.sleep(8)
        # Check status of both
        status1 = (await ac.get(f"/status/{ingestion_id1}")).json()
        status2 = (await ac.get(f"/status/{ingestion_id2}")).json()
        # First batch of MEDIUM should be completed, but second batch should be triggered or yet_to_start
        assert status1["batches"][0]["status"] in ("completed", "triggered")
        # HIGH priority should preempt and be triggered/completed before MEDIUM's second batch
        assert status2["batches"][0]["status"] in ("completed", "triggered")

        # Wait for all batches to complete
        await asyncio.sleep(15)
        status1 = (await ac.get(f"/status/{ingestion_id1}")).json()
        status2 = (await ac.get(f"/status/{ingestion_id2}")).json()
        assert all(b["status"] == "completed" for b in status1["batches"])
        assert all(b["status"] == "completed" for b in status2["batches"])

@pytest.mark.asyncio
async def test_batch_splitting_and_status_transitions():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/ingest", json={"ids": [10,11,12,13], "priority": "LOW"})
        ingestion_id = resp.json()["ingestion_id"]
        await asyncio.sleep(1)
        status = (await ac.get(f"/status/{ingestion_id}")).json()
        assert len(status["batches"]) == 2
        assert status["batches"][0]["ids"] == [10,11,12]
        assert status["batches"][1]["ids"] == [13]
        assert status["status"] in ("yet_to_start", "triggered")
        await asyncio.sleep(12)
        status = (await ac.get(f"/status/{ingestion_id}")).json()
        assert all(b["status"] == "completed" for b in status["batches"])
        assert status["status"] == "completed"

@pytest.mark.asyncio
async def test_invalid_ingestion_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/status/doesnotexist")
        assert resp.status_code == 404 