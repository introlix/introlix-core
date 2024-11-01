import os
import sys
import requests
from introlix_api.logger import logger
from introlix_api.exception import CustomException

# Define the URL of the API endpoint
DEV_DOT_TO_API = "https://dev.to/api/articles?tag={}&page={}&per_page={}"

def get_devDotTo_data(page: int = 1, per_page: int = 10, tag: int = '') -> dict:
    """
    Function to fetch data from the dev.to API.
    """
    try:
        # Construct the URL with the provided parameters
        url = DEV_DOT_TO_API.format(tag, page, per_page)
        response = requests.get(url)
        
        if response.status_code!= 200:
            logger.debug(f"Failed to fetch data from dev.to: {response.status_code}")
        
        # Convert the response to JSON
        articles = response.json()
        
        extracted_articles = [
            {
                "title": article["title"],
                "description": article["description"],
                "url": article["url"],
                "tags": article["tag_list"],
                "image": article["cover_image"],
                "created_at": article["created_at"]
            }
            for article in articles
            ]
        
        return extracted_articles
        
    except Exception as e:
        raise CustomException(e, sys) from e
    
def get_github_repo(page: int = 1, per_page: int = 10, tag: int = ''):
    """
    Function to fetch data from GitHub API.
    """
    try:
        # Construct the URL with the provided parameters
        url = f"https://api.github.com/search/repositories?q=topic:{tag}&sort=stars&page={page}&per_page={per_page}"
        response = requests.get(url)
        
        if response.status_code!= 200:
            logger.debug(f"Failed to fetch data from GitHub: {response.status_code}")
        
        # Convert the response to JSON
        repos = response.json()
        
        extracted_repos = [
            {
                "name": repo["name"],
                "description": repo["description"],
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "created_at": repo["created_at"]
            }
            for repo in repos["items"]
            ]
        
        return extracted_repos
        
    except Exception as e:
        raise CustomException(e, sys) from e

if __name__ == "__main__":
    print(get_devDotTo_data(1, 10))