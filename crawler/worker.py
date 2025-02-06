from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier): # GOOD
        """
        Initializes the crawler worker 

        @Parameters:
        worker_id - number to uniquely identify the crawler worker
        config    - used for the download function
        frontier  - used to maintain URLs that still need to be traversed
        """

        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
    
    def run(self): # [WIP]
        """
        Main crawler program where it keeps traversing the web using the frontier (which has an intial set of URLS) and
        only stops once its empty
        """

        while True:
            tbd_url = self.frontier.get_tbd_url() # Same as "popping" from queue
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            # TODO: Check if the URL is not duplicate and maintain depth number which is to used to avoid traps!

            resp = download(tbd_url, self.config, self.logger) # Requests for page/resource and will download it (which in the real-world would be saved in the document store)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp) # Will get next URLs to crawl (this should also include document content)
            for scraped_url in scraped_urls: # adding URLs to the frontier
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay) # Delay for politeness (should be set accordingly in "config.ini")
