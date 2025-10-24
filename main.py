from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from writerai import Writer
import os
from typing import Optional
import asyncio
from datetime import datetime, timedelta
import csv
import json
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(title="Text Summarizer API", version="1.0.0")

# Get CORS origins from environment variable or use defaults
cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:5174"
).split(",")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Writer client
# You'll need to set your WRITER_API_KEY environment variable
writer_client = Writer(api_key=os.getenv("WRITER_API_KEY"))


#
# Additional endpoint to get API info
@app.get("/")
async def get_home():
    """Get information about the API"""
    return {
        "name": "alex2",
        "version": "1.0.0",
        "description": "AI-powered text summarization using Writer SDK",
        "endpoints": {
            "/health": "Health check",
            "/api/summarize": "Summarize text (POST)",
            "/api/info": "API information",
        },
        "supported_styles": ["concise", "detailed", "bullet_points"],
    }


@app.get("/stream")
async def get_stream():
    """Stream current date every 2 seconds for one minute"""

    async def date_stream():
        """Generator function that yields current date every 2 seconds"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=60)  # 1 minute

        while datetime.now() < end_time:
            current_time = datetime.now()
            yield f"data: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        date_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/file-append")
async def file_append_endpoint(request: Request):
    """Append datetime, IP address, and user agent to data.csv and return CSV content as JSON"""
    
    # Get current datetime
    current_datetime = datetime.now().isoformat()
    
    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"
    
    # Get user agent
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Prepare CSV data
    csv_data = [current_datetime, client_ip, user_agent]
    
    # Define CSV file path
    csv_file_path = Path("data.csv")
    
    # Write header if file doesn't exist
    if not csv_file_path.exists():
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['datetime', 'ip_address', 'user_agent'])
    
    # Append new row
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_data)
    
    # Read and return CSV content as JSON
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        csv_content = list(csv_reader)
    
    return {
        "message": "Data appended successfully",
        "rows_added": 1,
        "total_rows": len(csv_content),
        "data": csv_content
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
