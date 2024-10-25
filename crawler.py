import sys
import time
import asyncio
from fastapi import APIRouter, HTTPException, Query
from introlix_api.crawler.bot import IntrolixBot, BotArgs
from introlix_api.exception import CustomException
from introlix_api.logger import logger
from introlix_api.app.database import search_data
from introlix_api.app.appwrite import fetch_root_sites, save_urls

router = APIRouter()

BATCH_SIZE = 10
urls_batch = []

def save_to_db(data):
    global urls_batch
    try:
        new_documents = []
        existing_urls = set()

        urls = [d["url"] for d in data]
        existing_documents = search_data.find({"url": {"$in": urls}})

        for doc in existing_documents:
            existing_urls.add(doc["url"])
        for d in data:
            # Check if the URL already exists in the database
            if d["url"] not in existing_urls:
                # If the URL does not exist, insert the data
                if d.get("content") is not None:
                    new_documents.append({
                        "url": d["url"],
                        "content": d["content"],
                    })

        if new_documents:
            search_data.insert_many(new_documents)

        if len(urls_batch) >  0:
            save_urls(urls_batch)
            urls_batch = []
    except Exception as e:
        raise CustomException(e, sys) from e
    
def extract_urls(batch_size=BATCH_SIZE):
    all_urls = []

    # Query the collection to get all documents
    documents = search_data.find()

    # Loop through each document and extract URLs in batches
    for doc in documents:
        # Check if 'content' and 'links' exist in the document
        if 'content' in doc and 'links' in doc['content']:
            # Extract URLs from the 'links' array
            urls = doc['content']['links']
            all_urls.extend(urls)

            # Yield URLs in batches to prevent memory overload
            if len(all_urls) >= batch_size:
                yield all_urls
                all_urls = []

    # Yield remaining URLs (if any)
    if all_urls:
        yield all_urls

def crawler(urls_batch):
    try:
        bot = IntrolixBot(urls=urls_batch, args=BotArgs)
        
        # Process each batch of scraped data
        for data_batch in bot.scrape_parallel(batch_size=BATCH_SIZE):
            save_to_db(data_batch)

    except Exception as e:
        raise CustomException(e, sys) from e
    
def run_crawler_continuously():
    global urls_batch
    try:
        first_run = 0
        while True:
            print(f"Running Crawler {first_run + 1} times")
            start_time = time.time()  # Record the start time

            while (time.time() - start_time) < 600:  # Run for 10 minutes (600 seconds)
                root_urls = fetch_root_sites()

                if root_urls:
                    logger.info(f"Starting crawler with {len(root_urls)} root URLs")
                    crawler(list(set(root_urls[::-1])))

                # Extract and process URLs in batches
                for extracted_urls in extract_urls(batch_size=BATCH_SIZE):
                    urls_batch.extend(list(set(extracted_urls)))
                    # logger.info(f"Starting crawler with {len(set(urls_batch))} extracted URLs from MongoDB")
                    # crawler(list(set(urls_batch)))

            # After 10 minutes, the while loop will restart without any pause
            logger.info("Restarting the crawler for another 10-minute session.")
    except Exception as e:
        raise CustomException(e, sys) from e


@router.post('/crawler')
def run_crawler():
    try:
        run_crawler_continuously()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

if __name__ == "__main__":
    while True:
        start_time = time.time()
        while (time.time() - start_time) < 600:
            run_crawler_continuously()
#     # urls = extract_urls()
#     # print(urls)