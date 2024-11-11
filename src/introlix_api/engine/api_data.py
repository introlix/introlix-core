from introlix_api.engine.third_party_apis import get_devDotTo_data, get_stack_overflow_data
from introlix_api.engine.graphql import fetch_hashnode_posts
from introlix_api.app.database import search_data
from introlix_api.utils.tags import fetch_tags
from introlix_api.logger import logger

def fetch_data(page: int = 1, per_page: int = 10, tag = ''):
    """
    Function to fetch data from multiple sources and combine them.
    """
    devDotTo_data = get_devDotTo_data(page, per_page, tag)
    hashnode_posts = fetch_hashnode_posts(page=page, per_page=per_page, tag=tag)

    # Combine the fetched data
    if hashnode_posts and devDotTo_data:
        combined_data = devDotTo_data + hashnode_posts
    elif hashnode_posts:
        data = []
    
        for item in hashnode_posts:
            new_entry = {
                "url": item["url"],
                "content": {
                    "title": item["title"],
                    "desc": item["description"],
                    "image": item["image"],
                    "tags": item["tags"],
                    "vote": 0,
                    "created_at": item["created_at"],
                },
                "type": item["type"]
            }
            data.append(new_entry)
        return data
    elif devDotTo_data:
        data = []
    
        for item in devDotTo_data:
            new_entry = {
                "url": item["url"],
                "content": {
                    "title": item["title"],
                    "desc": item["description"],
                    "image": item["image"],
                    "tags": item["tags"],
                    "vote": 0,
                    "created_at": item["created_at"]
                },
                "type": item["type"]
            }
            data.append(new_entry)
        return data
    else:
        return []

    data = []
    
    for item in combined_data:
        new_entry = {
            "url": item["url"],
            "content": {
                "title": item["title"],
                "desc": item["description"],
                "image": item["image"],
                "tags": item["tags"],
                "vote": 0,
                "created_at": item["created_at"]
            },
            "type": item["type"]
        }
        data.append(new_entry)
        
    return data

def fetch_discussion(page: int = 1, per_page: int = 10, tag: str = ''):
    """
    Function to fetch data from Stack Overflow API.
    """
    stack_overflow_data = get_stack_overflow_data(page=page, per_page=per_page, tag=tag)
    data = []

    for item in stack_overflow_data:
        new_entry = {
            "url": item["url"],
            "content": {
                "title": item["title"],
                "tags": item["tags"],
                "vote": 0,
                "created_at": item["created_at"],
                "answer_count": item["answer_count"],
            },
            "type": item["type"]
        }
        data.append(new_entry)

    return data



def batch_converter(lst: list, batch_size: int):
    """
    Convert list into batches of a specified size.

    Args:
        list (list): list to convert
        batch_size (int): size of the batch
    """
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]

if __name__ == '__main__':
    for tag in fetch_tags():
        data = fetch_discussion(page=1, per_page=10, tag=tag)
        if data:
            urls = [d["url"] for d in data]

            existing_urls = {doc["url"] for doc in search_data.find({"url": {"$in": urls}})}

            for d in data:
                if d["url"] not in existing_urls:
                    search_data.insert_one(d)
        else:
            logger.debug("No data to save")

            
    for page_no in range(1, 1001):
        data = fetch_data(page=page_no)
        if data:
            for batch in batch_converter(data, batch_size=100):
                urls = [d["url"] for d in data]

                existing_urls = {doc["url"] for doc in search_data.find({"url": {"$in": urls}})}

                for d in batch:
                    if d["url"] not in existing_urls:
                        search_data.insert_one(d)
        else:
            logger.debug("No data to save")