import re
from urllib.parse import urlparse, urljoin, urldefrag, parse_qs
from bs4 import BeautifulSoup
from collections import defaultdict

"""
https://ics.uci.edu/events/month/2050-01/
^ Format of the ics calendar. Need to deal with the infinite loop
What I did was keep track of the parent paths (ex: https://ics.uci.edu/events/month/) and if the count exceeds the max then it is disregarded
"""

MAX_URL_LIMIT = 100
MIN_LEN = 600
visited_parents = defaultdict(int) # [parent_url: count]

def scraper(url, resp):
    links = extract_next_links(url, resp)
    valid_links = [link for link in links if is_valid(link)]
        
    return valid_links

def extract_next_links(url, resp):
    '''
    Params:
        url: the URL that was used to get the page
        resp.url: the actual url of the page
        resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
        resp.error: when status is not 200, you can check the error here, if needed.
        resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
                resp.raw_response.url: the url, again
                resp.raw_response.content: the content of the page!
    Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    '''
    abs_links = []
    
    # Detect redirects and use the final URL for crawling
    final_url = resp.url
    if final_url != url:
        print(f'Redirect detected from {url} to {final_url}')
        url = final_url

    # Avoid crawling very large files
    content_length = resp.raw_response.headers.get('Content-Length')
    if content_length and int(content_length) > 10**6:  # Limit set to 1MB
        print(f'Skipping large file at {url} with size {content_length} bytes.')
        return []
    
    # Parse the HTML content of the page
    soup = BeautifulSoup(resp.raw_response.content, "lxml")

    # Avoid files with little content
    text = soup.get_text(separator=" ", strip=True)
    if len(text) < MIN_LEN:
        return []

    # Find all anchor tags that contain an href (specifies hyperlink) attribute
    all_links = soup.find_all('a', href=True)

    for link in all_links:
        href = link['href']
        # Convert to absolute URLS (urljoin handles when href is already absolute)
        abs_url = urljoin(url, href)
        # Remove fragment
        abs_url = urldefrag(abs_url)[0]

        abs_links.append(abs_url)
    
    return abs_links

def is_valid(url):
    '''
    Decide whether to crawl this url or not. 
    If you decide to crawl it, return True; otherwise return False.
    There are already some conditions that return False.
    '''
    
    try:
        file_extensions = ( r"\.(css|js|bmp|gif|jpe?g|ico|img|png|tiff?|mid|mp2|mp3|mp4|"
                          r"wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|pptx|doc|"
                          r"docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|"
                          r"epub|dll|cnf|tgz|sha1|thmx|mso|arff|rtf|jar|csv|rm|smil|wmv|swf|"
                          r"wma|zip|rar|gz|war)$" )
        file_extensions_common = r"(jpg|jpeg|png|gif|bmp|ico|pdf|doc|docx|ppt|pptx|xls|xlsx|txt|rtf|mp3|mp4|wav|ogg|avi|mov|wmv|zip|rar|tar|gz|7z|css|js|html|csv)"
        
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Allow only URLs from the specified domains
        valid_domains = {".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"}
        # Check if authority (aka netloc) ends with valid domains
        if not any(parsed.netloc.endswith(domain) for domain in valid_domains):
            return False
        
        '''
        Quality checks
        '''
        # Exclude "uploads", "files", or known low-information-value pages
        low_value_patterns = ["uploads", "files", "sort=", "filter=", "ref=", "session_id=", "edit"]
        if any(pattern in parsed.path.lower() or pattern in parsed.query.lower() for pattern in low_value_patterns):
            return False
        
        '''
        File checks
        '''
        # Exclude file extension as a path
        if re.match(r".*" + file_extensions, parsed.path.lower()):
            return False
        
        # Check the other parts for common file patterns
        if re.search(file_extensions_common, url):
            return False
        '''
        Trap prevention
        '''
        # Get the parent URL by removing the last part of the path
        parent_url = f"{parsed.netloc}{'/'.join(parsed.path.rstrip('/').split('/')[:-1])}"
        # Check the number of URLs visited for this authority-path pair
        visited_parents[parent_url] += 1
        
        # If the limit is exceeded, skip this URL
        if visited_parents[parent_url] >= MAX_URL_LIMIT:
            return False
        
        # Valid if bypassed all checks
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise