import random
import re
from fastapi import FastAPI, APIRouter, HTTPException, Request

from introlix_api.exception import CustomException
from introlix_api.app.database import startup_db_client, shutdown_db_client
from introlix_api.logger import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the database connection
    await startup_db_client(app)
    yield
    # Close the database connection
    await shutdown_db_client(app)

router = APIRouter()

# Preprocessing function to clean text
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove extra spaces, newlines, and tabs
    text = re.sub(r'\s+', ' ', text)
    # Remove punctuation (optional, depending on your data)
    text = re.sub(r'[^\w\s]', '', text)
    return text

@router.get('/similarity')
async def similarity(request: Request, page: int = 1, limit: int = 20, query: str = None):
    """
    Function to calculate cosine similarity between posts and a query.
    """
    try:
        # Ensure the query is provided
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")

        skip = (page - 1) * limit

        # Fetch posts from MongoDB
        response = await request.app.mongodb['feedData'].find().skip(skip).limit(limit).to_list(limit)

        # Filter out items that do not have both title and description
        response = [item for item in response if item.get('title') and item.get('desc')]

        # Convert ObjectId to string for MongoDB compatibility
        for item in response:
            item['_id'] = str(item['_id'])

        # Prepare document texts (title + desc) for similarity calculation
        posts_texts = [preprocess_text(item['title'] + ' ' + item['desc']) for item in response]

        # Preprocess the query
        query = preprocess_text(query)

        # Include the query at the start of the document list
        documents = [query] + posts_texts

        # Apply TF-IDF Vectorizer
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = vectorizer.fit_transform(documents)

        # Calculate cosine similarity between the query and the posts
        cosine_similarities = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()

        # Debugging: Print cosine similarity scores for better understanding
        print("Cosine Similarities:", cosine_similarities)

        # Lower the similarity threshold for short text comparisons
        similarity_threshold = 0.05

        # Filter posts that have a cosine similarity above the threshold
        similar_posts = [
            response[i] for i in range(len(response)) if cosine_similarities[i] >= similarity_threshold
        ]

        return similar_posts
    except Exception as e:
        raise HTTPException(status_code=400, detail=str)