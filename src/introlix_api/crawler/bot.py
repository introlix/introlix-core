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
from sentence_transformers import SentenceTransformer

from requests import ReadTimeout
from introlix_api.utils.core import html_to_dom
from introlix_api.app.appwrite import fetch_root_sites
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
        # self.model = SentenceTransformer('all-MiniLM-L6-v2')

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
                        for root_url in fetch_root_sites():
                            root_url_parsed = urlparse(root_url)
                            href_parsed = urlparse(href)
                            root_url_parsed_netloc = root_url_parsed.netloc
                            href_netloc = href_parsed.netloc
                            
                            # Debugging lines
                            logger.info(f"Checking href domain: {href_netloc} against root domain: {root_url_parsed_netloc}")
                            
                            if root_url_parsed_netloc == href_netloc:
                                urls.append(href)
                                break
                            
            return list(set(urls))
            
        except Exception as e:
            logger.info(f"Error occured while getting urls from page {e}")
            return []
            # raise CustomException(e, sys) from e

    # def get_desc(self, url: str) -> str:
    #     """
    #     Function to get the description of a page.

    #     Args:
    #         url (str): URL of the page.
    #     Returns:
    #         str: desc of the page.
    #     """
    #     try:
    #         status_code, content = self.fetch(url)

    #         if status_code != 200:
    #             return []

    #         soup = BeautifulSoup(content, 'html.parser')
    #         urls = []

    #         desc = soup.find('meta', attrs={'name': 'description'})

    #         if desc:
    #             desc = desc.get('content')
                
    #             return desc

    #         return ''
            
    #     except Exception as e:
    #         logger.info(f"Error occured while getting urls from page {e}")
    #         return []

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


            desc_element = dom.xpath("//meta[@name='description']")
            desc = ""
            if len(desc_element) > 0:
                desc_text = desc_element[0].get('content')
                if desc_text is not None:
                    desc = desc_text.strip()

            new_links = self.get_urls_from_page(url)
            new_links = list(set(new_links))

            return {
                'url': url,
                'content': {
                    'title': title,
                    # 'vector': self.model.encode(title).tolist(),
                    'desc': desc,
                    'links': sorted(new_links)
                },
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

    def scrape_parallel(self, batch_size: int):
        """
        Process scrape in parallel using multiprocessing.

        Args:
            urls (list): List of site URLs to process.
            batch_size (int): Number of URLs to process in each batch.
        Returns:
            
        """
        num_workers = max(1, os.cpu_count() // 2)
        # getting urls in batch
        batch_url = list(self.batch_converter(self.urls, batch_size))

        # Create a multiprocessing pool
        with multiprocessing.Pool(processes=num_workers) as pool:
            for batch in batch_url:
                results = pool.map(self.scrape, batch)
                # data = list([sublist for sublist in results])

                yield results
            
    def get_urls_from_page_parallel(self, urls: list, batch_size: int) -> list:
        """
        Process get_urls_from_page in parallel using multiprocessing.

        Args:
            urls (list): List of site URLs to process.
            batch_size (int): Number of URLs to process in each batch.
        Returns:
            list: List of fetched URLs.
        """
        num_workers = max(1, os.cpu_count() // 2)
        fetched_urls = []

        # getting urls in batch
        batch_url = list(self.batch_converter(urls, batch_size))

        # Create a multiprocessing pool
        with multiprocessing.Pool(processes=num_workers) as pool:
            for batch in batch_url:
                results = pool.map(self.get_urls_from_page, batch)
                return list([url for sublist in results for url in sublist])

        # return list(set(list(fetched_urls)))

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