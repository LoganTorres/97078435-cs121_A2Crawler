import re
from urllib.parse import urlparse, urljoin, urldefrag, parse_qs
from bs4 import BeautifulSoup
from collections import defaultdict

MIN_LEN = 200

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
    parsed = urlparse(url)
    
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
        print(f"little content: {url}")
        return []

    # Find all anchor tags that contain an href (specifies hyperlink) attribute
    all_links = soup.find_all('a', href=True)

    for link in all_links:
        href = link['href']
        # Deal with the staff pages (ex https://ics.uci.edu/~iftekha/)
        if len(parsed.path.strip('/').split('/')) == 1 and parsed.path.startswith('/~') and url[-1] != '/':
            url = url + '/'
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
        file_extensions = ( r".*\.(css|js|bmp|gif|jpe?g|ico|img|png|tiff?|mid|mp2|mp3|mp4|"
                          r"wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|pptx|doc|"
                          r"docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|"
                          r"epub|dll|cnf|tgz|sha1|thmx|mso|arff|rtf|jar|csv|rm|smil|wmv|swf|"
                          r"wma|zip|rar|gz|war|apk|mpg|bam|emx|bib|shar|lif|ppsx|wvx|odc|pps|xml|fig|dtd|sql|java|cp|sh|svg|conf|ipynb|json|scm|ff|py)$" )
        
        gitlab_avoids = ["commit", "compare", "tags", "blame", "merge_requests", "tree"]
        domain_avoids = ["containers.ics.uci.edu", "jujube.ics.uci.edu", "observium.ics.uci.edu", "chime.ics.uci.edu", 
                        "dblp.ics.uci.edu", "checkmate.ics.uci.edu", "duke.ics.uci.edu", "contact.ics.uci.edu", "tippers.ics.uci.edu"]

        # Avoid calendar events (want to keep regular event pages)
        # YYYY-MM-DD or YYYY/MM/DD
        # YYYY-DD-MM or YYYY/DD/MM
        # DD-MM-YYYY or DD/MM/YYYY
        # MM-DD-YYYY or MM/DD/YYYY
        # MM-YYYY or MM/YYYY
        # YYYY-MM or YYYY/MM
        date_pattern = r"(?=.*events)(?=.*(?:\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}|\d{2}[-/]\d{2}[-/]\d{4}|\d{2}[-/]\d{2}[-/]\d{4}|\d{2}[-/]\d{2}|\d{4}[-/]\d{2}))"
        
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Allow only URLs from the specified domains
        valid_domains = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"]
        # Check if authority (aka netloc) ends with valid domains
        if not any(parsed.netloc.endswith(domain) for domain in valid_domains):
            return False
        
        '''
        Quality checks
        '''
        # Exclude "uploads", "files", or known low-information-value pages
        low_value_patterns = ["uploads", "files=", "ref=", "session_id=", "=edit", "login", "account_activation", "/pdf/", "image=", "tribe_events",
        "prefs", "ical=", "calendar", "tribe-bar-date", "version=", "=diff", "=download", "share=", "zip-attachment", "JMEPopupWeb", "raw-attachment", "rev="]
        if any(pattern in parsed.path.lower() or pattern in parsed.query.lower() for pattern in low_value_patterns):
            return False
        # Don't want individual commits from gitlab
        if parsed.netloc == "gitlab.ics.uci.edu" and any(term in parsed.path for term in gitlab_avoids):
            return False
        # These domains are known to stall
        if parsed.netloc in domain_avoids:
            return False
        
        '''
        File checks
        '''
        # Exclude file extensions in params and query
        if re.match(file_extensions, parsed.path.lower()) or re.match(file_extensions, parsed.query.lower()):
            return False
        # Avoid txt from these paths since they are all data or code examples with little textual information
        if re.search(r'(~wjohnson|~babaks|~jacobson|bibtex|~stasio|~kay|~seal).*\.txt$', parsed.path.lower()):
            return False
        
        '''
        Trap prevention
        '''
        # Check if there is event date pattern
        if re.search(date_pattern, url):
            return False
        
        # Valid if bypassed all checks
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise