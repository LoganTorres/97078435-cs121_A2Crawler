from threading import Thread
from inspect import getsource
from utils.download import download
from utils import get_logger
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import scraper
import time
import re
import hashlib

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
        self._fingerprints = set() # Use to store the fingerprints which is used for near duplication detection!

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
            
            is_near_duplicate = False
            fingerprint = self._getFingerprint(resp)
            # Calculate the Hamming distance to each existing fingerprint
            for fp in self._fingerprints:
                distance = sum(1 for b1, b2 in zip(fp, fingerprint) if b1 != b2)
                # If distance is small enough, count as duplicate
                if distance < 20: #IDK WHAT TO ACTUALLY PUT HERE
                    is_near_duplicate = True
                    break

            if not is_near_duplicate:
                for scraped_url in scraper.scraper(tbd_url, resp): # adding URLs to the frontier
                    self.frontier.add_url(scraped_url)
                
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay) # Delay for politeness

    @classmethod
    def _getFingerprint(resp): # SimHash
        """
        Class method that simply gets create a finger print for the given response 'resp'

        @Parameters:
        resp - The response from the cache server which is used to create the fingerprint for near duplication detection

        @Returns:
        Returns a fingerprint which is used for determining near duplication with other fingerprints in self._fingerprints
        """

        webContent = BeautifulSoup(resp.raw_response.content, "html.parser").get_text()

        # Some stopping words (I think small set like this should be fine)
        stoppingWords = {"the", "of", "a", "how", "when", "at", "is", "to"}

        # Will remove the HTML in 'resp' and tokenize the content while filtering out stopping words
        tokens = [token for token in tokenize(webContent) if not (token in stoppingWords)] 

        # Initialize the vector to represent the fingerprint (128 bits)
        vector = [0] * 128

        for token in tokens:
            # Get the hash value for each token
            token_hash = hashlib.md5(token.encode('utf-8')).hexdigest()
            # Convert hash to binary (this will be a string of 128 characters '0' or '1')
            hash_bits = bin(int(token_hash, 16))[2:].zfill(128)

            # Update the vector based on the hash bits
            for i, bit in enumerate(hash_bits):
                # If the bit is '1', increment the corresponding dimension of the vector, else decrement it
                if bit == '1':
                    vector[i] += 1
                else:
                    vector[i] -= 1

        # Create the final SimHash by converting the vector into a binary string
        simhash = ''.join(['1' if x > 0 else '0' for x in vector])

        # Convert the binary string into a hexadecimal string (the final fingerprint)
        fingerprint = format(int(simhash, 2), '032x')

        return fingerprint

def tokenize(path: str) -> list[str]: # can replace with someone else's
    '''
    Reads a text file and returns a list of alphanumeric tokens in that file.

    Runtime Complexity:
    O(n) where n is the number of characters in a file.
    '''
    tokens = []
    try:
        # Open the file, replacing improperly encoded chars with placeholder
        with open(path, 'r', encoding='utf-8', errors='replace') as file:
            for line in file:
                # Convert to lowercase, get list of substrings matching regex pattern
                line_tokens = re.findall(r'[a-zA-Z0-9]+', line.lower())
                # Add the new tokens to the tokens object
                tokens.extend(line_tokens)
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
    except Exception as e:
        print(f"Error while processing file: {e}.")

    return tokens