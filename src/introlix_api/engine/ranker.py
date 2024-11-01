from introlix_api.engine.third_party_apis import get_devDotTo_data
from introlix_api.engine.graphql import fetch_hashnode_posts

def fetch_data(page: int = 1, per_page: int = 10, tag = ''):
    """
    Function to fetch data from multiple sources and combine them.
    """
    devDotTo_data = get_devDotTo_data(page, per_page, tag)
    hashnode_posts = fetch_hashnode_posts(page=page, per_page=per_page, tag=tag)

    # Combine the fetched data
    combined_data = devDotTo_data + hashnode_posts

    return combined_data

print(fetch_data(tag="web3"))