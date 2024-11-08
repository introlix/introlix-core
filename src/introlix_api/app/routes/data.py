import pytz
from dateutil import parser
from datetime import datetime, timezone
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

def normalize_date(date_str):
    try:
        # Attempt to parse as ISO format with timezone
        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        # If fromisoformat fails, fall back to a more flexible parser
        try:
            date_obj = parser.parse(date_str)
        except (ValueError, TypeError):
            print(f"Warning: Unrecognized date format for '{date_str}'")
            return None  # Return None or handle the invalid date as needed

    # Convert to UTC and return in ISO format
    return date_obj.astimezone(pytz.UTC)

@router.get('/posts', response_model=List[FeedModel])
async def fetch_data(request: Request, tags: List[str], page: int = 1, limit: int = 20):
    """
    Function to fetch posts based on pagination, query, and sorting options.
    """
    try:
        skip = (page - 1) * limit
        query = {"content.tags": {"$in": tags}}  # Updated query to match any tag in the list
        response = await request.app.mongodb['search_data'].find(query).skip(skip).limit(limit).to_list(limit)

        current_date = datetime.now(timezone.utc)
        hotness_ranked_posts = []

        for item in response:
            item["_id"] = str(item['_id'])
            item["title"] = item['content'].get('title', '')
            item["desc"] = item['content'].get('desc', '')
            item["url"] = item.get('url', '')
            item["image_url"] = item['content'].get('image', '') or ""
            item["tags"] = item['content'].get('tags', [])
            item["vote"] = item['content'].get('vote', 0)

            # Handle created_at normalization
            created_at_str = item['content'].get('created_at', '')
            if created_at_str in [None, "No date found"]:
                created_at = current_date
            else:
                created_at = normalize_date(created_at_str)

            # Ensure created_at is a datetime object; if None, skip the calculation
            if created_at:
                # Calculate age in hours
                age_hours = (current_date - created_at).total_seconds() / 3600

                # Hotness ranking formula
                rank = (item["vote"] - 1) / ((age_hours + 2) ** 1.5)
                item["rank"] = rank
            else:
                # If created_at is invalid, set rank low
                item["rank"] = float('-inf')

            item["created_at"] = created_at.isoformat() if created_at else "Unknown"
            hotness_ranked_posts.append(item)

        hotness_ranked_posts.sort(key=lambda x: x["rank"], reverse=False)
        return hotness_ranked_posts

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
