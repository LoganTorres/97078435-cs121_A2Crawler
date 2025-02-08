from threading import Thread
from inspect import getsource
from utils.download import download
from utils import get_logger
from urllib.robotparser import RobotFileParser
# from bs4 import BeautifulSoup
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
        self._visitedURLS = set() # To avoid entering the same URLs (exact duplication check)
        # self._fingerprints = set() # Use to store the fingerprints which is used for near duplication detection!

        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
    
    def run(self): # GOOD
        """
        Main crawler program where it keeps traversing the web using the frontier (which has an intial set of URLS) and
        only stops once its empty
        """

        # Robot parser so that we can read "robots.txt" for each URL's domain we get from the frontier
        robotFileParser = RobotFileParser()
        currentDomain = None

        while True:
            tbd_url = self.frontier.get_tbd_url() # Similar in a way as if we were "popping" from a queue
            
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            # Get current domain
            start = tbd_url.find("//")
            urlDomain = tbd_url[:tbd_url.find("/", start + 2)]

            # If the domain changes (or is None), then get the robots.txt file for the new domain!
            if((currentDomain == None) or (currentDomain != urlDomain)):
                robotFileParser.set_url(urlDomain + "/robots.txt") # Get the robots.txt file from the domain in which 'tbd_url' is from
                robotFileParser.read() # Parse content from robots.txt so that we can check if the crawler may crawl 'tbd_url'
                currentDomain = urlDomain

                # get crawl delay and if it exits then use that delay, else just use 1 (default delay)!
                crawlDelay = robotFileParser.crawl_delay(self.config.user_agent)
                self.config.time_delay = crawlDelay or 1

            # If we've visited the URL before then ignore it and move on to the next URL!
            # Additionally check if we can crawl the URL (not doing so will surely lead to a crawler trap!)
            if((tbd_url in self._visitedURLS) or not robotFileParser.can_fetch(self.config.user_agent, tbd_url)): continue

            self._visitedURLS.add(tbd_url) # Add to visited URLs set!

            resp = download(tbd_url, self.config, self.logger) # Requests for page/resource and will download it (which in the real-world would be saved in the document store)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            # fingerPrint = self._getFingerprint(resp)
           
            # # If not a near duplication, then scrap and extract valid next URLs and place in froniter!
            # if(not (fingerPrint in self._fingerprints)):
            #     self._fingerprints.add(fingerPrint)

            for scraped_url in scraper.scraper(tbd_url, resp): # adding URLs to the frontier
                self.frontier.add_url(scraped_url)
                
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay) # Delay for politeness

    # @classmethod
    # def _getFingerprint(resp): # [WIP]
    #     """
    #     Class method that simply gets create a finger print for the given response 'resp'

    #     @Parameters:
    #     resp - The response from the cache server which is used to create the fingerprint for near duplication detection

    #     @Returns:
    #     Returns a fingerprint which is used for determining near duplication with other fingerprints in self._fingerprints
    #     """

    #     webContent = BeautifulSoup(resp.raw_response.content, "html.parser").get_text()

    #     # Some stopping words (I think small set like this should be fine)
    #     stoppingWords = {"the", "of", "a", "how", "when", "at", "is", "to"}

    #     # Will remove the HTML in 'resp' and tokenize the content while filtering out stopping words
    #     tokens = [token for token in tokenize(webContent) if not (token in stoppingWords)] 
    #     # TODO:                replace ^^^ "tokenize" with the name of the tokenize function from A1
    #     tokens = [hash(token) for token in tokens]

    #     selectedTokens = [select min tokens]

