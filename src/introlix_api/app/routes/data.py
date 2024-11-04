import re
from fastapi import FastAPI, APIRouter, HTTPException, Request
from introlix_api.exception import CustomException
from introlix_api.app.database import startup_db_client, shutdown_db_client
from introlix_api.app.model import FeedModel
from contextlib import asynccontextmanager
from typing import List

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the database connection
    await startup_db_client(app)
    yield
    # Close the database connection
    await shutdown_db_client(app)

router = APIRouter()

@router.get('/posts', response_model=List[FeedModel])
async def fetch_data(request: Request, tag: str, page: int = 1, limit: int = 20):
    """
    Function to fetch posts based on pagination, query, and sorting options.
    """
    try:
        skip = (page - 1) * limit

        query = {"content.tags": tag}
        response = await request.app.mongodb['search_data'].find(query).skip(skip).limit(limit).to_list(limit)

        for item in response:
            item["_id"]=str(item['_id'])
            item["title"]=item['content'].get('title', '')
            item["desc"]=item['content'].get('desc', '')
            item["url"]=item.get('url', '')
            if item['content'].get('image', '') != None:
                item["image_url"]=item['content'].get('image', '')
            else:
                item["image_url"]=""
            item["tags"]=item['content'].get('tags', [])
            item["vote"]=item['content'].get('vote', 0)
            item["created_at"]=item['content'].get('created_at', '')

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=str)