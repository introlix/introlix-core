def fun():        
        all_urls = set(self.urls) # list of all urls
        visited_urls = set()       # To keep track of visited URLs
        current_urls = self.urls   # The URLs to process in the current level

        logger.info(f"Fetching new urls from {len(current_urls)}")
        new_urls = self.get_urls_from_page_parallel(current_urls, batch_size)

        current_urls = new_urls
        logger.info(f"New urls fetched: {len(current_urls)}")
        all_urls.update(set(new_urls))
        logger.info(f"All url len {all_urls}")

        logger.info(f"Now Fetching new urls from {len(current_urls)}")
        new_urls = self.get_urls_from_page_parallel(current_urls, batch_size)

        current_urls = new_urls
        logger.info(f"New urls fetched: {len(current_urls)}")
        all_urls.update(set(new_urls))
        logger.info(f"All url len {all_urls}")