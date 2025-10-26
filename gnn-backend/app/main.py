import sys
import redis
from fastapi import FastAPI

version = f"{sys.version_info.major}.{sys.version_info.minor}"


app = FastAPI()

# Connect to Redis
# redis_client = redis.Redis(host='localhost', port=6379, db=0)

@app.get("/")
async def read_root():
    message = f"Hello world! From FastAPI running on Uvicorn with Gunicorn. Using Python {version}"
    return {"message": message}

