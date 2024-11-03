import re
import sys
import time
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Query
from introlix_api.crawler.bot import IntrolixBot, BotArgs
from introlix_api.exception import CustomException
from introlix_api.logger import logger
from introlix_api.app.database import search_data
from introlix_api.app.appwrite import fetch_root_sites, fetch_saved_urls, save_urls

router = APIRouter()

BATCH_SIZE = 10
urls_batch = []

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
        urls = [d["url"] for d in data if filter_urls(d["url"])]
        existing_urls = {doc["url"] for doc in search_data.find({"url": {"$in": urls}})}

        # Use a generator to only keep new documents that need to be inserted
        new_documents = (
            {"url": d["url"], "content": d["content"]}
            for d in data
            if d["url"] not in existing_urls and d.get("content") is not None
        )

        # Insert documents if there are any to add
        new_docs_list = list(new_documents)

        if new_docs_list:
            search_data.insert_many(new_docs_list)

        # Save URLs if urls_batch is not empty
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
                root_urls = fetch_root_sites()
                saved_urls = fetch_saved_urls()

                urls = root_urls + saved_urls
                urls = list(set(urls))

                if urls:
                    logger.info(f"Starting crawler with {len(urls)} root URLs")
                    crawler(urls[::-1])

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