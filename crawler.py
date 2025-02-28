import re
import sys
import time
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Query
from introlix_api.crawler.bot import IntrolixBot, BotArgs
from introlix_api.exception import CustomException
from introlix_api.logger import logger
from introlix_api.utils.root_sites import root_sites
from introlix_api.app.database import search_data, db
from introlix_api.app.appwrite import fetch_root_sites, fetch_saved_urls, save_urls
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

router = APIRouter()

BATCH_SIZE = 10
urls_batch = []
storage_threshold = 500 * 1024 * 1024
delete_batch = 1000

def filter_urls(url: str) -> bool:
    """
    A function to filter non article urls from the scraped urls
    Args:
        url (list): url
    Returns:
        bool: True if the url is article url else False
    """
    parsed_url = urlparse(url)

    if parsed_url.path in ('', '/'):
        return False
    
    non_article_keywords = [
        "/product", "/products", "/home", "/item", "/items", "/category", "/categories",
        "/login", "/signin", "/logout", "/signup", "/register", "/account", "/user",
        "/profile", "/dashboard", "/settings", "/preferences", "/order", "/orders",
        "/cart", "/checkout", "/payment", "/subscribe", "/subscription",
        "/contact", "/support", "/help", "/faq", "/about", "/privacy", "/terms",
        "/policy", "/conditions", "/legal", "/service", "/services", "/guide",
        "/how-to", "/pricing", "/price", "fees", "/plans", "/features", "/partners",
        "/team", "/careers", "/jobs", "/join", "/apply", "/training", "/demo",
        "/trial", "/download", "/install", "/app", "/apps", "/software", "/portal",
        "/index", "/main", "/video", "/videos", "/photo", "/photos",
        "/image", "/images", "/gallery", "/portfolio", "/showcase", "/testimonials",
        "/reviews", "/search", "/find", "/browse", "/list", "/tags", "/explore",
        "/new", "/trending", "/latest", "/promotions", "/offers", "/deals", "/discount",
        "/coupon", "/coupons", "/gift", "/store", "/stores", "/locator", "/locations",
        "/branches", "/events", "/webinar", "/calendar", "/schedule",
        "/class", "/classes", "/lesson", "/lessons", "/training", "/activity",
        "/activities", "/workshop", "/exhibit", "/performance", "/map", "/directions",
        "/weather", "/traffic", "/rates", "/auction", "/bid", "/tender", "/investment",
        "/loan", "/mortgage", "/property", "/real-estate", "/construction", "/project",
        "/client", "/clients", "/partner", "/sponsor", "/media", "/press", "/releases",
        "/announcements", "/newsroom", "/resources", "courses", "collections", "/u/", "/members/",
        "/@", "/shop", "/wiki", "/author", "/dynamic", "/image", "/submit"  # TODO: need to add more
    ]

    article_keywords = [
        "/blog/", "post", "article", "insights", "guide", "tutorial",
        "how-to", "what", "how", "introduction", "/news/"
    ]

    article_pattern = [
        r'/(/blog/|article|articles|post|posts|blogs|news|)/\d{4}/\d{2}/+[a-z0-9-]+/?',
        r'/(/blog/|article|articles|post|posts|blogs|news|)/[a-z0-9-]+/[a-z0-9-]+',
        r'(?<!\/\/www)(/blog/|article|articles|post|posts|blogs|news|)/[a-z0-9-]+',
        r'^(?!.*\/category\/).*\/[a-z0-9-]+\/[a-z0-9-]+(-[a-z0-9-]+)+$',
        r'/[^/]+/\d{4}/\d{2}/\d{2}/+[a-z0-9]+/?',
        r'/[^/]+/\d{4}/\d{2}/+[a-z0-9]+/?'
        r'/[a-z0-9-]+/\d{4}/\d{2}/+/?',
        r'/[a-z0-9-]+/\d{4}/\d{2}/\d{2}/+/?'
    ]

    for pattern in article_pattern:
        if re.search(pattern, url):
            if not any(keyword in url for keyword in non_article_keywords):
                return True
            
    if any (keyword in url for keyword in article_keywords):
        return True
    
    last_segment = parsed_url.path.strip('/').split('/')[-1]
    if '-' in last_segment and len(last_segment.split('-')) > 2:
        return True
    
    return False

def save_to_db(data):
    global urls_batch
    try:
        # Check database storage size and delete old documents if needed
        stats = db.command("collStats", "search_data")
        storage_size = stats['size']

        if storage_size >= storage_threshold:
            oldest_docs = search_data.find().sort("createdAt", ASCENDING).limit(delete_batch)
            oldest_ids = [doc['_id'] for doc in oldest_docs]
            search_data.delete_many({"_id": {"$in": oldest_ids}})

        # Prepare list of URLs to check in the database
        urls = [d["url"] for d in data if filter_urls(d["url"])]

        # Retrieve existing URLs from the database to filter out duplicates
        existing_urls = set(search_data.find({"url": {"$in": urls}}).distinct("url"))

        # Filter out documents with URLs that already exist in the database
        unique_data = [
            {"url": d["url"], "content": d["content"], "type": "article"}
            for d in data
            if d["url"] not in existing_urls and d.get("content") is not None
        ]

        # Insert only unique documents
        if unique_data:
            try:
                search_data.insert_many(unique_data)
            except DuplicateKeyError as e:
                logger.info("Duplicate URL detected during insertion. Skipping duplicate entries.")

        # Process URLs in `urls_batch` if it has URLs
        if urls_batch:
            try:
                save_urls(urls_batch)
            except Exception as e:
                logger.error(f"Error saving URLs to Appwrite: {str(e)}")
            urls_batch.clear()

    except Exception as e:
        raise CustomException(e, sys) from e
    
def extract_urls(batch_size=BATCH_SIZE):
    # Fetch documents with required fields only, reducing memory footprint per document
    documents = search_data.find({}, {"content.links": 1})

    # Initialize a list to store URLs in batches
    batch_urls = []

    for doc in documents:
        # Extract URLs only if 'content' and 'links' exist
        links = doc.get("content", {}).get("links")
        if links:
            # Use a generator to iterate over links directly
            for url in links:
                batch_urls.append(url)
                # Yield URLs in batches to control memory usage
                if len(batch_urls) >= batch_size:
                    yield batch_urls
                    batch_urls = []  # Clear the batch after yielding

    # Yield any remaining URLs
    if batch_urls:
        yield batch_urls

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
        while True:
            start_time = time.time()  # Record the start time

            while (time.time() - start_time) < 600:  # Run for 10 minutes (600 seconds)
                try:
                    root_urls = fetch_root_sites()
                    saved_urls = fetch_saved_urls()
                except Exception as e:
                    logger.info("Error fetching URLs from Appwrite: %s", str(e))
                    root_urls = []
                    saved_urls = []

                if root_urls and saved_urls:
                    urls = root_urls + saved_urls
                    urls = list(set(urls))
                else:
                    urls = root_sites() + urls_batch

                if urls:
                    logger.info(f"Starting crawler with {len(urls)} root URLs")
                    crawler(urls[::-1])


                # Extract and process URLs in batches
                for extracted_urls in extract_urls(batch_size=BATCH_SIZE):
                    urls_batch.extend(list(set(extracted_urls)))
                    # logger.info(f"Starting crawler with {len(set(urls_batch))} extracted URLs from MongoDB")
                    # crawler(list(set(urls_batch)))
                time.sleep(1)

            time.sleep(1)

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