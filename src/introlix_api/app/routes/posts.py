from bson import ObjectId
import pytz
from dateutil import parser
from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter, HTTPException, Request, Query
from introlix_api.app.database import votes
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
async def fetch_data(request: Request, tags: List[str] = Query(...), page: int = 1, limit: int = 20):
    """
    Function to fetch posts based on pagination, query, and sorting options.
    """
    try:
        skip = (page - 1) * limit
        query = {
            "content.tags": {"$in": tags},
            "type": "article"
        }
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
    
@router.get('/discussion')
async def fetch_disscussion(request: Request, tags: List[str] = Query(...), page: int = 1, limit: int = 20):
    """
    Function to fetch discussion based on pagination, query, and sorting options.
    """
    try:
        skip = (page - 1) * limit
        query = {
            "content.tags": {"$in": tags},
            "type": "discussion"
        }
        response = await request.app.mongodb['search_data'].find(query).skip(skip).limit(limit).to_list(limit)

        current_date = datetime.now(timezone.utc)
        hotness_ranked_posts = []

        for item in response:
            item["_id"] = str(item['_id'])
            item["title"] = item['content'].get('title', '')
            item["url"] = item.get('url', '')
            item["tags"] = item['content'].get('tags', [])
            item["vote"] = item['content'].get('vote', 0)
            item["answer_count"] = item['content'].get('answer_count', 0)

            # Handle created_at normalization
            created_at_str = item['content'].get('created_at', '')
            created_at_str = datetime.utcfromtimestamp(created_at_str)
            if created_at_str in [None, "No date found"]:
                created_at = current_date
            else:
                created_at = normalize_date(str(created_at_str))

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

@router.post('/vote')
async def vote(request: Request, vote: int, post_id: str = Query(...), user_id: str = Query(...)):
    """
    Function to vote for a post.
    """
    try:
        post_id = ObjectId(post_id)

        # Check if the user has already voted for the post
        result = await request.app.mongodb['votes'].find_one({"user_id": user_id, "post_id": post_id, "vote": vote})

        if result:
            votes.delete_one({
                "_id": result["_id"]
            })
        else:
            existing_vote = await request.app.mongodb['votes'].find_one({"user_id": user_id, "post_id": post_id})
            if existing_vote:
                votes.delete_one({
                "_id": existing_vote["_id"]
                })

            votes.insert_one({
                "post_id": post_id,
                "user_id": user_id,
                "vote": vote
            })

        # counting total vote
         # Calculate the total vote count for the post
        total_votes = await request.app.mongodb['votes'].aggregate([
            {"$match": {"post_id": post_id}},
            {"$group": {"_id": "$post_id", "total_votes": {"$sum": "$vote"}}}
        ]).to_list(length=1)

        # Extract the total vote count or default to 0 if no votes are found
        vote_count = total_votes[0]["total_votes"] if total_votes else 0

        # Update the vote count in the post document
        await request.app.mongodb['search_data'].update_one(
            {"_id": post_id},
            {"$set": {"content.vote": vote_count}}
        )

        return {"message": f"Vote submitted successfully with total vote {vote_count}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/hasvoted')
async def hasVote(request: Request, post_id: str = Query(...), user_id: str = Query(...)):
    """
    Function to check if the user has already voted for a post.
    """
    try:
        post_id = ObjectId(post_id)

        existing_vote = await request.app.mongodb['votes'].find_one({"user_id": user_id, "post_id": post_id})

        if existing_vote:
            return {"has_voted": True, "vote": existing_vote['vote']}
        else:
            return {"has_voted": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))