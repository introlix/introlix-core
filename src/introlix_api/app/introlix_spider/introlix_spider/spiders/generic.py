import os
import re
import scrapy
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import asyncio
from dotenv import load_dotenv, dotenv_values
from introlix_api.app.database import feed_data, db
from introlix_api.app.appwrite import fetch_root_sites


load_dotenv()


class GenericSpider(scrapy.Spider):
    """
    Spider to crawl internet to get data to display it on introlix feed
    """
    name = "generic"

    def __init__(self, *args, **kwargs):
        super(GenericSpider, self).__init__(*args, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=10)  # Control parallelism

        self.data = []

        self.all_urls = fetch_root_sites()
        self.domain_pattern = r'(?:[a-z0-9-]+\.)?([a-z0-9-]+\.[a-z]{2,})(?:\/|$)'
        
        self.allowed_domains = []
        self.start_urls = []
        self.CLASSIFICATION_API = os.getenv('CLASSIFICATION_API')

        for url in self.all_urls:
            result = re.search(self.domain_pattern, url)

            if result:
                self.allowed_domains.append(result.group(1))
                self.start_urls.append(result.group(1))

    def start_requests(self):
        for url in self.all_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def is_this_article(self, url):
        """
        Function to verify if the url is article url or not
        """

        # list of article url patterns
        article_pattern = [
            r'/(blog|article|articles|post|blog|posts|blogs|)/\d{4}/\d{2}/+[a-z0-9-]+/?',
            r'/(blog|article|articles|post|blog|posts|blogs|)/[a-z0-9-]+/[a-z0-9-]+',
            r'(?<!\/\/www)(blog|article|articles|post|posts|blogs)/[a-z0-9-]+',
            r'^(?!.*\/category\/).*\/[a-z0-9-]+\/[a-z0-9-]+(-[a-z0-9-]+)+$',
            r'/[^/]+/\d{4}/\d{2}/\d{2}/+[a-z0-9]+/?',
            r'/[^/]+/\d{4}/\d{2}/+[a-z0-9]+/?'
            r'/[a-z0-9-]+/\d{4}/\d{2}/+/?',
            r'/[a-z0-9-]+/\d{4}/\d{2}/\d{2}/+/?'
         ]

        # list of non article keywords
        non_article_words = [
            "category", "signup", "login", "about", "contact",  # Add more non-article keywords...
        ]

        # Check if the url matches any of the article patterns
        for pattern in article_pattern:
            if re.search(pattern, url):
                if not any(word in url for word in non_article_words):
                    return True
        return False

    def parse(self, response):
        # Get all the urls from the response
        urls = response.css('a::attr(href)').extract()

        # Filter out the urls that are not article urls
        article_urls = [response.urljoin(url.split("?")[0]) for url in urls if self.is_this_article(url)]

        # Send a request to each article url
        for url in article_urls:
            yield scrapy.Request(url=url, callback=self.parse_article)

    async def classify_article(self, text):
        """
        function to classify the article
        """
        classify_ai = self.CLASSIFICATION_API
        payload = {"text": text}

        # Send a request to the classification API
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(classify_ai, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result.get('category', 'Unknown')
            except aiohttp.ClientError as e:
                self.logger.error(f"Error making request to classification API: {e}")
                return 'Error'

    async def parse_article(self, response):
        """
        Function to get all details of the article
        """
        hostname = response.url.split("/")[2] # getting the website name of the article
        title = response.css("h1::text").get() # getting the title of the article
        url = response.url # getting the url of the article
        desc = response.css('meta[name="description"]::attr(content)').get() # getting the description of the article
        publication_date = response.css('span::text, time::text').re_first(r'(\w+ \d+|\d+\s?\w+,? \w+)') # getting the publication date of the article
        image_url = response.css('meta[property="og:image"]::attr(content)').get() # getting the image url of the article

        # Classify article title asynchronously
        category = await self.classify_article(title) # getting the category of the article from the classification API

        # Prepare feed item
        feed_items = {
            "title": title,
            "desc": desc,
            "url": url,
            "publication_date": publication_date,
            "image_url": image_url,
            "category": category,
            "source": hostname
        }

        self.data.append(feed_items)

    def closed(self, reason):
        print(f"Spider closed: {reason}")
        print("Saving ----")
        self.save_data()

    def save_data(self):
        # if "feed_Data" in db.list_collection_names():
        #     feed_data.drop()

        for feed_items in self.data:
            feed_data.insert_one(feed_items)


# import re
# import scrapy
# from pathlib import Path
# import requests
# from concurrent.futures import ThreadPoolExecutor
# from twisted.internet.defer import ensureDeferred
# from introlix_api.app.database import feed_data, db
# from introlix_api.app.appwrite import fetch_root_sites


# class GenericSpider(scrapy.Spider):
#     name = "generic"

#     def __init__(self, *args, **kwargs):
#         super(GenericSpider, self).__init__(*args, **kwargs)
#         self.executor = ThreadPoolExecutor(max_workers=10)

#         self.data = []

#         self.all_urls = fetch_root_sites()
#         self.domain_pattern = r'(?:[a-z0-9-]+\.)?([a-z0-9-]+\.[a-z]{2,})(?:\/|$)'
        
#         self.allowed_domains = []
#         self.start_urls = []

#         for url in self.all_urls:
#             result = re.search(self.domain_pattern, url)

#             if result:
#                 self.allowed_domains.append(result.group(1))
#                 self.start_urls.append(result.group(1))

#     def start_requests(self):

#         for url in self.all_urls:
#             yield scrapy.Request(url=url, callback=self.parse)

#     def is_this_article(self, url):
#         article_pattern = [
#             r'/(blog|article|articles|post|blog|posts|blogs|)/\d{4}/\d{2}/+[a-z0-9-]+/?',
#             r'/(blog|article|articles|post|blog|posts|blogs|)/[a-z0-9-]+/[a-z0-9-]+',
#             r'(?<!\/\/www)(blog|article|articles|post|posts|blogs)/[a-z0-9-]+',
#             r'^(?!.*\/category\/).*\/[a-z0-9-]+\/[a-z0-9-]+(-[a-z0-9-]+)+$',
#             r'/[^/]+/\d{4}/\d{2}/\d{2}/+[a-z0-9]+/?',
#             r'/[^/]+/\d{4}/\d{2}/+[a-z0-9]+/?'
#             r'/[a-z0-9-]+/\d{4}/\d{2}/+/?',
#             r'/[a-z0-9-]+/\d{4}/\d{2}/\d{2}/+/?'
#         ]

#         # List of non-article keywords
#         non_article_words = [
#             "category",
#             "signup",
#             "login",
#             "about",
#             "contact",
#             "privacy",
#             "terms",
#             "faq",
#             "help",
#             "support",
#             "user",
#             "account",
#             "settings",
#             "profile",
#             "admin",
#             "dashboard",
#             "search",
#             "index",
#             "topics",
#             "rss",
#             "solutions",
#             "shows",
#             "author"
#         ]

#         for pattern in article_pattern:
#             if re.search(pattern, url):
#                 for word in non_article_words:
#                     if word in url:
#                         return False
#                 return True
#         return False

#     def parse(self, response):
#         urls = response.css('a::attr(href)').extract()

#         article_urls = [response.urljoin(url.split("?")[0]) for url in urls if self.is_this_article(url)]

#         for url in article_urls:
#             yield scrapy.Request(url=url, callback=self.parse_article)

#     def classify_article(self, text):
#         classify_ai = "dont show api"
#         payload = {"text": text}

#         try:
#             response = requests.post(classify_ai, json=payload)
#             response.raise_for_status()
#             return response.json().get('category', 'Unknown')
#         except requests.RequestException as e:
#             self.logger.error(f"Error making request to classification API: {e}")
#             return 'Error'
    
#     def parse_article(self, response):
#         # getting all the infomation from the article

#         hostname = response.url.split("/")[2]


#         title = response.css("h1::text").get()
#         url = response.url
#         desc = response.css('meta[name="description"]::attr(content)').get()
#         publication_date = response.css('span::text, time::text').re_first(r'(\w+ \d+|\d+\s?\w+,? \w+)')
#         image_url = response.css('meta[property="og:image"]::attr(content)').get()

#         # Using ThreadPoolExecutor to classify the title in a separate thread
#         future = self.executor.submit(self.classify_article, title)
#         category = future.result()

#         # storing the infomation on mongodb
#         feed_items = {
#             "title": title,
#             "desc": desc,
#             "url": url,
#             "publication_date": publication_date,
#             "image_url": image_url,
#             "category": category,
#             "source": hostname
#         }

#         self.data.append(feed_items)

#     def closed(self, reason):
#         print(f"Spider closed: {reason}")
#         print("Saving ----")
#         self.save_data()

#     def save_data(self):
#         if "feed_Data" in db.list_collection_names():
#             feed_data.drop()

#         for feed_items in self.data:
#             feed_data.insert_one(feed_items)