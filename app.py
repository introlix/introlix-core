from fastapi import FastAPI, Query, HTTPException
from bson import ObjectId
import sys
import httpx
import os
import random
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from introlix_api.app.routes import auth, run_spider, similarity
from typing import List
from dotenv import load_dotenv, dotenv_values

from introlix_api.app.appwrite import databases, APPWRITE_DATABASE_ID, ID, APPWRITE_ACCOUNT_COLLECTION_ID, get_interests
from introlix_api.app.database import startup_db_client, shutdown_db_client
from introlix_api.ml.recommendation import Recommendation

from introlix_api.exception import CustomException

from contextlib import asynccontextmanager

from pydantic import BaseModel, Field

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

class FeedModel(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    desc: str
    url: str
    publication_date: str
    image_url: str
    category: str
    source: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the database connection
    await startup_db_client(app)
    yield
    # Close the database connection
    await shutdown_db_client(app)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url='/docs')

@app.get("/feed_data", response_model=List[FeedModel])
async def get_feed_data(page: int = 1, limit: int = 20, user_id: str = Query(...), category=None):
    try:
        skip = (page - 1) * limit

        interests = get_interests()
        # getting only the interests not keywords
        user_interests = interests['interests']

        users = databases.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_ACCOUNT_COLLECTION_ID
        )
        
        for doc in users['documents']:
            if user_id == doc['$id']:
                user_interests = doc['interests']
        
        user_interests = [item.split(':')[1] for item in user_interests]
        response = await app.mongodb['feedData'].find({"category": {"$in": user_interests}}).skip(skip).limit(limit).to_list(limit)

        # random.shuffle(response)

        # Filter out items that do not have a title
        response = [item for item in response if item.get('title')]
        response = [item for item in response if item.get('desc')]

        # Perform the aggregation
        # if category == None:
        #     # response = await app.mongodb['feedData'].find({"category": {"$in": user_interests}}).skip(skip).limit(limit).to_list(limit)
        # else:
            
        #     # response = await app.mongodb['feedData'].find({"category": category}).skip(skip).limit(limit).to_list(limit)

        article_titles = [item['title'] for item in response]
        recommendation_system = Recommendation(user_interests, article_titles)
        recommended_titles = recommendation_system.recommend()

        response = [post for post in response if post['title'] in recommended_titles]


        for item in response:
            item['_id'] = str(item['_id'])
            item['title'] = item.get('title') or ''
            item['desc'] = item.get('desc') or ''
            item['url'] = item.get('url') or ''
            item['publication_date'] = item.get('publication_date') or ''
            item['image_url'] = item.get('image_url') or ''
            item['category'] = item.get('category') or ''
            item['source'] = item.get('source') or ''

        return response
    except Exception as e:
        raise CustomException(e, sys) from e
    
@app.get("/fetch_post", response_model=FeedModel)
async def get_feed_data(post_id: str = Query(...)):
    try:
        post_id = ObjectId(post_id)
        response = await app.mongodb['feedData'].find_one({"_id": post_id})

        if not response:
            raise HTTPException(status_code=404, detail="Post not found")

        # Convert _id to string
        response["_id"] = str(response["_id"])

        # Check for null values and set defaults if needed
        response["desc"] = (response.get("desc") or "No Description")[:90]
        response["publication_date"] = response.get("publication_date") or "Unknown Date"
        response["image_url"] = response.get("image_url") or "No Image URL"
        response["category"] = response.get("category") or "Uncategorized"
        response["source"] = response.get("source") or "Unknown Source"

        # for item in response:
        #     item['title'] = item.get('title') or ''
        #     item['desc'] = item.get('desc') or ''
        #     item['url'] = item.get('url') or ''
        #     item['publication_date'] = item.get('publication_date') or ''
        #     item['image_url'] = item.get('image_url') or ''
        #     item['category'] = item.get('category') or ''
        #     item['source'] = item.get('source') or ''

        return response
    except Exception as e:
        raise CustomException(e, sys) from e
    
@app.get("/test_recommendation")
async def test_recommendation(
    user_interests: list[str] = Query(..., description="Comma-separated list of user interests"),
    articles: list[str] = Query(..., description="Comma-separated list of articles")
):
    """
    Test endpoint for recommendations.
    Takes user interests and articles as query parameters and returns recommended articles.
    """

    # Create a recommendation instance
    recommendation = Recommendation(user_interests, articles)

    # Get the recommended articles
    recommended_articles = recommendation.recommend()

    return {
        "user_interests": user_interests,
        "recommended_articles": recommended_articles,
    }

@app.get("/youtube/videos")
async def get_youtube_videos(query: str = None):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "q": query or "trending",
        "type": "video",
        "maxResults": 10,
        "order": "viewCount"  # You can change this to 'date' for recent uploads
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    
app.include_router(auth.router, prefix="/auth")
app.include_router(run_spider.router, prefix="/spider")
app.include_router(similarity.router, prefix="/feed")