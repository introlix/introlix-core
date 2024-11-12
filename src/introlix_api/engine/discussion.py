from introlix_api.engine.third_party_apis import get_stack_overflow_data
from introlix_api.utils.tags import fetch_tags
from introlix_api.logger import logger
from introlix_api.app.database import search_data

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