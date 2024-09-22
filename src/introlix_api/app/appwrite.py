import os
import sys
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from dotenv import load_dotenv, dotenv_values

from introlix_api.logger import logger
from introlix_api.exception import CustomException

from pydantic import HttpUrl

load_dotenv()

APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")
APPWRITE_ROOTSITES_COLLECTION_ID = os.getenv("APPWRITE_ROOTSITES_COLLECTION_ID")
APPWRITE_ACCOUNT_COLLECTION_ID = os.getenv("APPWRITE_ACCOUNT_COLLECTION_ID")

client = Client()
client.set_endpoint('https://cloud.appwrite.io/v1')
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)

databases = Databases(client)

# models for database
class RootSitesModel:
    url: HttpUrl

# fetching the data from appwrite
def fetch_root_sites():
    """
    Function to fetch the root sites from appwrite
    """
    try:
        logger.info("Fetching all of the root sites...")
        response = databases.list_documents(database_id=APPWRITE_DATABASE_ID,collection_id=APPWRITE_ROOTSITES_COLLECTION_ID) # fetching all of the root sites

        root_sites = [root_site['url'] for root_site in response['documents']] # extracting the urls
    
        return root_sites
    
    except Exception as e:
        raise CustomException(e, sys) from e