import os
import json
import asyncio
from bson import ObjectId
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from introlix_api.app.database import search_data
from algoliasearch.search.client import SearchClientSync
from dotenv import load_dotenv

load_dotenv()

ALGOLIA_USER = os.getenv("ALGOLIA_USER")
ALGOLIA_KEY = os.getenv("ALGOLIA_KEY")
INDEX_NAME = "introlix_data"

# Initialize the Algolia client
_client = SearchClientSync(ALGOLIA_USER, ALGOLIA_KEY)

def convert_object_ids(doc):
    """Recursively convert ObjectId fields to strings in the document."""
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            convert_object_ids(value)  # Recursively convert in nested dicts
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    convert_object_ids(item)  # Recursively convert in dicts within lists
    return doc

async def upload_data():
    """Uploads data to Algolia in batches, updating records by setting `objectID` to prevent duplicates."""
    batch_size = 1000
    batch = []
    
    cursor = search_data.find()
    for doc in cursor:
        # Convert any ObjectId fields to strings for JSON compatibility
        doc = convert_object_ids(doc)
        
        # Set `objectID` to ensure uniqueness and prevent duplicates
        doc['objectID'] = str(doc['_id'])  # Using MongoDB _id as `objectID`

        # Convert document to JSON string and check its size
        doc_json = json.dumps(doc)
        doc_size = len(doc_json.encode('utf-8'))

        # Only add to batch if size is within Algolia's 10 KB limit
        if doc_size <= 10000:
            batch.append(doc)

        # Send batch to Algolia when the batch size is reached
        if len(batch) >= batch_size:
            _client.save_objects(index_name=INDEX_NAME, objects=batch)
            batch.clear()  # Clear the batch after sending

    # Send any remaining documents
    if batch:
        _client.save_objects(index_name=INDEX_NAME, objects=batch)

    print("Uploaded data to Algolia.")

async def main():
    # Run the upload function immediately
    await upload_data()
    
    scheduler = AsyncIOScheduler()
    # Schedule `upload_data` to run every 4 hours
    scheduler.add_job(upload_data, 'interval', hours=4)
    scheduler.start()

    print("Scheduler started. Uploading data to Algolia every 4 hours.")
    
    # Keep the main thread alive to allow scheduled tasks to run
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
