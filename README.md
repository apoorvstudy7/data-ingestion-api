# Data Ingestion API

A FastAPI-based application for asynchronous, rate-limited data ingestion with priority-based batch processing.

## Features

- Asynchronous data ingestion
- Priority-based batch processing
- Rate limiting
- Real-time status tracking
- Modern web interface

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python -m uvicorn main:app --reload
```

3. Access the application:
- Frontend: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Deployment on Render.com

1. Create a new account on [Render.com](https://render.com)

2. Create a new Web Service:
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - Name: `data-ingestion-api` (or your preferred name)
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - Plan: Free

3. Add Environment Variables:
   - `ENVIRONMENT`: `production`
   - `FRONTEND_URL`: Your Render.com URL (will be provided after deployment)

4. Click "Create Web Service"

The application will be automatically deployed and you'll get a URL like `https://your-app-name.onrender.com`

## API Endpoints

- `POST /ingest`: Submit new data for ingestion
- `GET /status/{ingestion_id}`: Check ingestion status
- `GET /recent`: Get recent ingestion submissions

## Testing

Run tests using pytest:
```bash
pytest
```

## Design Choices
- **FastAPI** for async-friendly, modern API development.
- **Threading** for background batch processing.
- **In-memory store** for demo simplicity (swap for DB/Redis for production).
- **Priority Queue** ensures correct batch order.
- **No real external API calls**; simulated with `time.sleep`.

## Notes
- No authentication required.
- All logic is in-memory; restarting the server clears all data.
- See `