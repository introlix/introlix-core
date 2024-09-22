import sys
import subprocess
from fastapi import APIRouter, HTTPException, Query

from introlix_api.exception import CustomException
from introlix_api.logger import logger

router = APIRouter()

@router.post('/run_spider')
async def run_spider():
    """
    Function to run the introlix spider
    """
    try:
        command = ["scrapy", "crawl", "generic"] # command to run the spider
        working_directory = "src/introlix_api/app/introlix_spider" # directory to run the spider

        result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True) # run the spider

        return result.stdout, result.stderr
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))