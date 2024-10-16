import os, sys, re, time
import requests
import multiprocessing
from bs4 import BeautifulSoup
from dataclasses import dataclass
from introlix_api.logger import logger
from urllib.parse import urlparse, urlunsplit, urljoin
from urllib.robotparser import RobotFileParser
from introlix_api.exception import CustomException
from urllib.robotparser import RobotFileParser

from requests import ReadTimeout
from introlix_api.utils.core import html_to_dom
from ssl import SSLCertVerificationError
from urllib3.exceptions import NewConnectionError, MaxRetryError

@dataclass
class BotArgs:
    TIMEOUT_SECONDS = 3
    MAX_FETCH_SIZE = 1024*1024
    MAX_DEEP_SIZE = 100
    MAX_DATA_SIZE = MAX_DEEP_SIZE * 20
    MAX_URL_LENGTH = 150
    BAD_URL_REGEX = re.compile(r'\/\/localhost\b|\.jpg$|\.png$|\.js$|\.gz$|\.zip$|\.pdf$|\.bz2$|\.ipynb$|\.py$')
    GOOD_URL_REGEX = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)')
    DEFAULT_ENCODING = 'utf8'
    DEFAULT_ENC_ERRORS = 'replace'
    ALLOWED_EXCEPTIONS = (ValueError, ConnectionError, ReadTimeout, TimeoutError,
                      OSError, NewConnectionError, MaxRetryError, SSLCertVerificationError)

class IntrolixBot:
    def __init__(self, urls: list, args: BotArgs, is_sitemap: bool = True, look_for_rss: bool = True, obey_robots_txt: bool = True):
        """
        Initialize the IntrolixBot.

        Args:
            urls (list): List of URLs to scrape.
            is_sitemap (bool, optional): Whether the URLs are sitemaps. Defaults to True.
            look_for_rss (bool, optional): Whether to look for RSS feeds. Defaults to True.
            obey_robots_txt (bool, optional): Whether to obey robots.txt. Defaults to True.
        """
        self.urls = urls
        self.is_sitemap = is_sitemap
        self.look_for_rss = look_for_rss
        self.obey_robots_txt = obey_robots_txt
        self.sitemaps = []
        self.pages = []
        self.data = []

        # bot args
        self.TIMEOUT_SECONDS = args.TIMEOUT_SECONDS
        self.MAX_FETCH_SIZE = args.MAX_FETCH_SIZE
        self.MAX_URL_LENGTH = args.MAX_URL_LENGTH
        self.BAD_URL_REGEX = args.BAD_URL_REGEX
        self.GOOD_URL_REGEX = args.GOOD_URL_REGEX
        self.DEFAULT_ENCODING = args.DEFAULT_ENCODING
        self.DEFAULT_ENC_ERRORS = args.DEFAULT_ENC_ERRORS
        self.ALLOWED_EXCEPTIONS = args.ALLOWED_EXCEPTIONS
        self.MAX_DEEP_SIZE = args.MAX_DEEP_SIZE
        self.MAX_DATA_SIZE = args.MAX_DATA_SIZE

        # Initialize trackers
        self.current_data_size = 0  # Track total data size
        self.current_depth = {}  # Track the number of pages fetched for each URL

        # for url in self.urls:
        #     url_pages = self.get_urls_from_page(url)
        #     self.pages.extend(url_pages)

        #     # scraping the url
        #     for page in self.pages:
        #         self.data.append(self.scrape(page))

        # check if robots.txt is allows to crawl
        # if self.obey_robots_txt:
        #     for url in self.urls:
        #         allowed_to_crawl = self.see_robots_txt(url)
        #         if allowed_to_crawl:
        #             self.allowed_to_crawl_sites.append(url)
        #             logger.debug(f"Allowed to crawl {url}")
        #         else:
        #             logger.debug(f"Not allowed to crawl {url}")

    def fetch(self, url:str) -> tuple[int, bytes]:
        """
        Function to fetch a URL.

        Args:
            url (str): URL to fetch.
        Returns:
            tuple[int, bytes]: status code and content.
        """

        r = requests.get(url, stream=True, timeout=self.TIMEOUT_SECONDS)

        size = 0
        start = time.time()

        content = b""
        for chunk in r.iter_content(1024):
            if time.time() - start > self.TIMEOUT_SECONDS:
                raise ValueError('Timeout reached')

            content += chunk

            size += len(chunk)
            if size > self.MAX_FETCH_SIZE:
                logger.debug(f"Maximum size reached for URL {url}")
                break

        return r.status_code, content

    def see_robots_txt(self, url: str) -> bool:
        """
        Function to check if robots.txt allows this bot to crawl.

        Args:
            main_url (str): main root url of the site.
            url (str): URL to check.
        Returns:
            bool: True if the bot is allowed to crawl, False otherwise.
        """
        try:
            try:
                parsed_url = urlparse(url)
            except ValueError:
                logger.debug(f"Unable to parse URL: {url}")
                return False

            robots_url = urlunsplit((parsed_url.scheme, parsed_url.netloc, 'robots.txt', '', ''))
            parse_robots = RobotFileParser(robots_url)

            try:
                status_code, content = self.fetch(robots_url)
            except Exception as e:  # Catch all exceptions for now
                logger.debug(f"Robots error: {robots_url}, {e}")
                return True

            decoded = None
            for encoding in ['utf-8', 'iso-8859-1']:
                try:
                    decoded = content.decode(encoding).splitlines()
                    break
                except UnicodeDecodeError:
                    pass

            if decoded is None:
                logger.debug(f"Unable to decode robots file {robots_url}")
                return True

            parse_robots.parse(decoded)
            allowed = parse_robots.can_fetch('IntrolixBot', url)  # Your bot's name
            logger.debug(f"Robots allowed for {url}: {allowed} and {decoded} is decoded with {robots_url}")
            return allowed
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_urls_from_page(self, url: str) -> list:
        """
        Function to get all URLs from a page.

        Args:
            url (str): URL of the page.
        Returns:
            list: List of URLs from the page.
        """
        try:
            status_code, content = self.fetch(url)

            if status_code != 200:
                return []

            soup = BeautifulSoup(content, 'html.parser')
            urls = []

            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    if not href.startswith('http'):
                        href = urljoin(url, href)
                    # if not self.BAD_URL_REGEX.search(href):
                    #     href = href
                    if self.GOOD_URL_REGEX.search(href):
                        urls.append(href)
            return list(set(urls))
            
        except Exception as e:
            logger.info(f"Error occured while getting urls from page {e}")
            return []
            # raise CustomException(e, sys) from e

    def scrape(self, url: str) -> dict:
        """
        Function to scrape the site.

        Args:
            url (str): URL to scrape.
        Returns:
            dict: scraped data.
        """
        try:
            logger.info(f"Crawling URL {url}")
            js_timestamp = int(time.time() * 1000)

            if self.obey_robots_txt:
                allowed = self.see_robots_txt(url)

                if not allowed:
                    return {
                        'url': url,
                        'status': None,
                        'timestamp': js_timestamp,
                        'content': None,
                        'error': {
                            'name': 'RobotsDenied',
                            'message': 'Robots do not allow this URL',
                        }
                    }

            try:
                status_code, content = self.fetch(url)
            except self.ALLOWED_EXCEPTIONS as e:
                logger.debug(f"Exception crawling URl {url}: {e}")
                return {
                    'url': url,
                    'status': None,
                    'timestamp': js_timestamp,
                    'content': None,
                    'error': {
                        'name': 'AbortError',
                        'message': str(e),
                    }
                }

            if len(content) == 0:
                return {
                    'url': url,
                    'status': status_code,
                    'timestamp': js_timestamp,
                    'content': None,
                    'error': {
                        'name': 'NoResponseText',
                        'message': 'No response found',
                    }
                }

            try:
                dom = html_to_dom(content, self.DEFAULT_ENCODING, None, self.DEFAULT_ENC_ERRORS)
            except Exception as e:
                logger.exception(f"Error parsing dom: {url}")
                return {
                    'url': url,
                    'status': status_code,
                    'timestamp': js_timestamp,
                    'content': None,
                    'error': {
                    'name': e.__class__.__name__,
                    'message': str(e),
                }
            }
        
            title_element = dom.xpath("//title")
            title = ""
            if len(title_element) > 0:
                title_text = title_element[0].text
                if title_text is not None:
                    title = title_text.strip()

            return {
                'url': url,
                'status': status_code,
                'timestamp': js_timestamp,
                'content': {
                    'title': title,
                },
                'error': None
            }

        except Exception as e:
            raise CustomException(e, sys) from e

    def batch_converter(self, lst: list, batch_size: int):
        """
        Convert list into batches of a specified size.

        Args:
            list (list): list to convert
            batch_size (int): size of the batch
        """
        for i in range(0, len(lst), batch_size):
            yield lst[i:i + batch_size]

    def get_urls_from_page_parallel(self, urls: list, batch_size: int) -> list:
        """
        Process get_urls_from_page in parallel using multiprocessing.

        Args:
            urls (list): List of site URLs to process.
            batch_size (int): Number of URLs to process in each batch.
        Returns:
            list: List of fetched URLs.
        """
        num_workers = multiprocessing.cpu_count()
        fetched_urls = []

        # getting urls in batch
        batch_url = list(self.batch_converter(urls, batch_size))

        # Create a multiprocessing pool
        with multiprocessing.Pool(processes=num_workers) as pool:
            for batch in batch_url:
                results = pool.map(self.get_urls_from_page, batch)
                fetched_urls.extend([url for sublist in results for url in sublist])

        return list(set(list(fetched_urls)))

    def scrape_parallel(self, urls: list, batch_size: int) -> dict:
        """
        Process scrape in parallel using multiprocessing.

        Args:
            urls (list): List of site URLs to process.
            batch_size (int): Number of URLs to process in each batch.
        Returns:
            dict: data.
        """
        num_workers = multiprocessing.cpu_count()
        data = []

        # getting urls in batch
        batch_url = list(self.batch_converter(urls, batch_size))

        # Create a multiprocessing pool
        with multiprocessing.Pool(processes=num_workers) as pool:
            for batch in batch_url:
                results = pool.map(self.scrape, batch)
                data.extend([sublist for sublist in results])

        return data

    def crawl(self, batch_size: int, deep: int = 10):
        """
        Function to crawl the site.

        Args:
            batch_size (int): batch size of the initial urls.
            deep (int): How deep from a site data show be fetched.
        """

        all_urls = self.urls
        current_urls = self.urls

        while True:
            new_urls = self.get_urls_from_page_parallel(current_urls, batch_size)
            new_urls = list(set(new_urls))
            logger.info(f"Fetched New urls len {len(new_urls)}")
            current_urls_set = set(new_urls) - set(all_urls)
            all_urls.extend(new_urls)
            current_urls = list(current_urls_set)

            # If no new URLs are found, break the loop
            if not current_urls_set:
                logger.info("No new URLs found, exiting the loop.")
                break

            logger.info(f"Current urls len {len(current_urls)}")
            logger.info(f"All urls len is {len(all_urls)}")

            # logger.info(f"Fetched New urls are {new_urls}")

        # for level in range(deep):
        #     logger.info(f"Starting level {level + 1}/{deep}. URLs to process: {len(current_urls)}")
        #     logger.info(f"Current URLs being processed: {current_urls}")
        #     new_urls = self.get_urls_from_page_parallel(current_urls, batch_size)
        #     new_urls = set(new_urls)

        #     logger.info(f"Fetched {len(new_urls)} URLs from current level.")
            
        #     # Remove already visited URLs to avoid duplicate crawling
        #     new_urls_before_dedup = len(new_urls)
        #     new_urls = new_urls - visited_urls
        #     logger.info(f"New URLs after deduplication: {len(new_urls)} out of {new_urls_before_dedup}")

        #     # If no new URLs are found, stop the crawling
        #     if not new_urls:
        #         logger.info("No new URLs found. Stopping crawl.")
        #         break

        #     # Add newly found URLs to the global set of all URLs
        #     all_urls.update(new_urls)

        #     # Mark the current URLs as visited
        #     visited_urls.update(current_urls)

        #     # Prepare for the next level of crawling
        #     current_urls = list(new_urls)

        #     # Log the current state of URLs after processing
        #     logger.info(f"Current URLs updated for next level: {current_urls}")
        #     logger.info(f"Total visited URLs so far: {len(visited_urls)}")
        #     logger.info(f"Total unique URLs found so far: {len(all_urls)}")

        #     logger.info(f"Finished level {level + 1}")

        # return list(all_urls)
        # url_pages = []

        # print(url_pages)
        # print("----------------")

        # url_pages = self.get_urls_from_page_parallel(self.urls, batch_size)

        # print(len(url_pages))
        # print(len(set(url_pages)))

        # print(url_pages)


        # for url in self.urls:
        #     if url not in self.current_depth:
        #         self.current_depth[url] = 0  # Initialize depth for each URL

            # Fetch URLs from the page
            # url_pages.extend(self.get_urls_from_page(url))


            # Only fetch if we haven't exceeded MAX_DEEP_SIZE for this URL
            # for page in url_pages:
            #     if self.current_depth[url] >= self.MAX_DEEP_SIZE:
            #         logger.info(f"Max depth reached for {url}. Stopping further fetches.")
            #         break
                
            #     if page != None:
            #         print(page)
            #         url_pages.extend(self.get_urls_from_page(page))

            # for page in url_pages:
            #     if self.current_data_size >= self.MAX_DATA_SIZE:
            #         logger.info("Max data size reached. Stopping all further fetches.")
            #         return  # Exit if total data size exceeds the limit

            #     # Fetch and scrape the page
            #     page_data = self.scrape(page)

            #     # Add page data to list and update current data size
            #     self.pages.append(page)
            #     self.data.append(page_data)
            #     self.current_data_size += len(str(page_data))  # Estimate data size as string length

            #     # Increment depth for the current URL
            #     self.current_depth[url] += 1

            #     # Check if max data size reached after scraping this page
            #     if self.current_data_size >= self.MAX_DATA_SIZE:
            #         logger.info("Max data size reached during crawling. Stopping.")
            #         return