import sys
import time
from fastapi import APIRouter, HTTPException, Query
from introlix_api.crawler.bot import IntrolixBot, BotArgs
from introlix_api.exception import CustomException
from introlix_api.logger import logger
from introlix_api.app.database import search_data
from introlix_api.app.appwrite import fetch_root_sites

router = APIRouter()

def save_to_db(data):
    try:
        for d in data:
            # Check if the URL already exists in the database
            if not search_data.find_one({"url": d["url"]}):
                # If the URL does not exist, insert the data
                if d['content'] is not None:
                    search_data.insert_one({
                        "url": d["url"],
                        "content": d["content"],
                    })
            else:
                logger.info(f"Duplicate found. Skipping URL: {d['url']}")
    except Exception as e:
        raise CustomException(e, sys) from e
    
def extract_urls(batch_size=100):
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
        for data_batch in bot.scrape_parallel(batch_size=100):
            save_to_db(data_batch)

    except Exception as e:
        raise CustomException(e, sys) from e
    
def run_crawler_continuously():
    try:
        while True:
            root_urls = fetch_root_sites()

            if root_urls:
                logger.info(f"Starting crawler with {len(root_urls)} root URLs")
                crawler(root_urls)

            # Extract and process URLs in batches
            for urls_batch in extract_urls(batch_size=100):
                logger.info(f"Starting crawler with {len(set(urls_batch))} extracted URLs from MongoDB")
                crawler(list(set(urls_batch)))

            time.sleep(10)  # Wait before the next iteration
    except Exception as e:
        raise CustomException(e, sys) from e

@router.post('/crawler')
def run_crawler():
    try:
        run_crawler_continuously()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

# if __name__ == "__main__":
#     run_crawler_continuously()
#     # urls = extract_urls()
#     # print(urls)