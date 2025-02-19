from threading import Thread
from inspect import getsource
from utils.download import download
from utils import get_logger
import urllib
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
import scraper
import time
import re
import hashlib

STOPWORDS = {
    "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he",
    "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's",
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll",
    "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
    "your", "yours", "yourself", "yourselves"
}

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
        self._fingerprints = set()
        self.robots_cache = {}

        # For the report:
        self.visited_urls = set() # To avoid entering the same URLs and track # of unique URLs
        self.longest_page = ("", 0) # Track URL and word count of longest page
        self.word_counter = Counter() # Word counter across all pages
        self.subdomains = defaultdict(int) # track ics.uci.edu subdomains

        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
    
    def run(self):
        """
        Main crawler program where it keeps traversing the web using the frontier (which has an intial set of URLS) and
        only stops once its empty
        """

        while True:
            tbd_url = self.frontier.get_tbd_url() # Similar in a way as if we were "popping" from a queue
            
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            # Get url parts
            parsed_url = urlparse(tbd_url.replace(" ", ""))
            scheme = parsed_url.scheme
            netloc = parsed_url.netloc

            # Construct robot url
            robots_url = f"{scheme}://{netloc}/robots.txt"

            # If we've visited the URL before then ignore it and move on to the next URL!
            # Additionally check if we can crawl the URL
            if((tbd_url in self.visited_urls) or not self._can_fetch(tbd_url, robots_url)):
                self.frontier.mark_url_complete(tbd_url)
                continue

            resp = download(tbd_url, self.config, self.logger) # Requests for page/resource and will download it (which in the real-world would be saved in the document store)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            # Don't process bad status or no response
            if resp.status >= 400 or resp.status < 200 or resp.raw_response == None:
                self.frontier.mark_url_complete(tbd_url)
                time.sleep(self.config.time_delay) # Delays since I alr downloaded
                continue
            
            is_near_duplicate = False
            fingerprint = self._get_fingerprint(resp, tbd_url)
            # If fingerprint is None, link does not contain valuable info. Move on.
            if fingerprint is None:
                self.frontier.mark_url_complete(tbd_url)
                time.sleep(self.config.time_delay) # Delay for politeness
                continue
            
            if len(self._fingerprints) != 0:
                # Calculate the Hamming distance to each existing fingerprint
                for fp in self._fingerprints:
                    distance = sum(1 for b1, b2 in zip(fp, fingerprint) if b1 != b2)
                    # If distance is small enough, count as near duplicate
                    if distance <= 5:
                        print(f'Skipping {tbd_url} as its fingerprint is similar to another.')
                        is_near_duplicate = True
                        break

            if not is_near_duplicate:
                self._fingerprints.add(fingerprint) #Avoid adding to fingerprint set if it was a duplicate of another
                for scraped_url in scraper.scraper(tbd_url, resp): # adding URLs to the frontier
                    self.frontier.add_url(scraped_url)

            '''
            ics.uci.edu domain check and add url to valid list, includes duplicate fingerprint but not bad/low-content files
            '''
            # Extract the main domain by splitting at the last two parts
            domain_parts = netloc.split(".")
            # Check if the domain is ics.uci.edu
            if len(domain_parts) >= 3 and domain_parts[-3] == "ics" and domain_parts[-2] == "uci" and domain_parts[-1] == "edu":
                subdom = f"{scheme}://{netloc}"
                # Add 1 to subdomain count
                self.subdomains[subdom] += 1
            
            self.visited_urls.add(tbd_url) # Add URL to set if it made it to this point
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay) # Delay for politeness

    # Fetch or return cached RobotFileParser for a given URL.
    def _get_parser(self, robots_url):
        domain = urlparse(robots_url).netloc
        if domain not in self.robots_cache:
            # Use the provided download function instead of parser.read()
            resp = download(robots_url, self.config, self.logger)

            parser = RobotFileParser()
            # If good status and there is a response, parse with RobotFileParser
            if resp.status == 200 and resp.raw_response:
                parser.parse(resp.raw_response.text.splitlines())
                print(f"Downloading robots.txt for {domain}")
            # Otherwise, assume all urls allowed
            else:
                parser.allow_all = True
                print(f"robots.txt not found for {domain}, assuming all URLs are allowed.")

            self.robots_cache[domain] = parser
            time.sleep(self.config.time_delay)
        return self.robots_cache[domain]
    
    # Check if a URL is allowed for a given user agent.
    def _can_fetch(self, target_url, robots_url):
        parser = self._get_parser(robots_url)
        return parser.can_fetch(self.config.user_agent, target_url)

    # SimHash comparison
    def _get_fingerprint(self, resp, tbd_url):
        """
        Create a finger print for the given response 'resp'

        @Parameters:
        resp - The response from the cache server which is used to create the fingerprint for near duplication detection

        @Returns:
        Returns a fingerprint which is used for determining near duplication with other fingerprints in self._fingerprints
        """

        webContent = BeautifulSoup(resp.raw_response.content, "lxml").get_text(separator=" ", strip=True)

        # Get all the tokens, and same tokens but without stopwords
        tokens = tokenize(webContent)
        tokens_no_stopwords = [token for token in tokens if token not in STOPWORDS]

        stopword_count = len(tokens) - len(tokens_no_stopwords)
        stopword_ratio = stopword_count / len(tokens) if len(tokens) > 0 else 0

        # If too few stopwords <5%, likely not valid content.
        # High stopword ratios also excluded due to being likely spam.
        if stopword_ratio < 0.05 or stopword_ratio > 0.7:
            return None
        
        # Soft 404s
        if len(tokens) >= 3 and (tokens[:3] == ["page", "not", "found"] or tokens[0] == "error"):
            return None

        # Update Counter - no stopwords
        self.word_counter.update(tokens_no_stopwords)

        # If length is larger than current longest, update
        if len(tokens) > self.longest_page[1]:
            self.longest_page=(tbd_url, len(tokens))

        # Initialize the vector to represent the fingerprint (128 bits)
        vector = [0] * 128

        for token in tokens_no_stopwords:
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

def tokenize(text: str) -> list[str]: # can replace with someone else's
    '''
    Reads text and returns a list of alphanumeric tokens in that file.

    Runtime Complexity:
    O(n) where n is the number of characters in a file.
    '''
    try:
        # Convert the text to lowercase and get a list of alphanumeric + ' tokens using regex
        tokens = re.findall(r"[a-zA-Z0-9']+", text.lower())
        # Don't want single character tokens
        tokens = [token for token in tokens if len(token) > 1]
    except Exception as e:
        print(f"Error while processing text: {e}.")
        return []

    return tokens
