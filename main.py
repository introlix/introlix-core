import subprocess

def run_app():
    command = ["scrapy", "crawl", "generic"]
    working_directory = "src/introlix_api/app/introlix_spider"

    result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True)

    print("Output:", result.stdout)
    print("Error:", result.stderr)

if __name__ == "__main__":
    # running the spider
    run_app()

    # def run_get_urls_from_page_parallel(self, urls: list, max_workers: int=10) -> list:
    #     """
    #     Running get_urls_from_page function in parallel for many runs.

    #     Args:
    #         urls (list): list of urls
    #         max_workers (int, optional): number of workers. Defaults to 10.
    #     Returns:
    #         list: list of fetched urls
    #     """
    #     fetched_urls = []

    #     with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    #         futures = {executor.submit(self.get_urls_from_page, url): url for url in urls}

    #         for future in concurrent.futures.as_completed(futures):
    #             url = futures[future]

    #             try:
    #                 result = future.result()
    #                 fetched_urls.append(result)
    #             except Exception as e:
    #                 raise CustomException(e, sys) from e

    #     return list(set(list(url for sublist in fetched_urls if sublist is not None for url in sublist)))