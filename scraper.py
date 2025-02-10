import re
from urllib.parse import urlparse, urljoin, urldefrag, parse_qs
from bs4 import BeautifulSoup

MIN_LEN = 600

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
    valid_links = []

    # Check if status of page is 200, if not print the error message
    if resp.status >= 400 or resp.status < 200:
        print(f'Error: Recieved status {resp.status}.')
        return []
    
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

        if is_valid(abs_url):
            valid_links.append(abs_url)
    
    return valid_links

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
        
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Allow only URLs from the specified domains
        valid_domains = {".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"}
        # Check if authority (aka netloc) ends with valid domains
        if not any(parsed.netloc.endswith(domain) for domain in valid_domains):
            return False
        
        # Exclude "uploads", "files", or known low-information-value pages
        low_value_patterns = ["uploads", "files", "sort=", "filter=", "ref=", "session_id="]
        if any(pattern in parsed.path.lower() or pattern in parsed.query.lower() for pattern in low_value_patterns):
            return False
        
        # Exclude file extension as a path
        if re.match(r".*" + file_extensions, parsed.path.lower()):
            return False
        
        # Check the query string for image file extensions (e.g., image=someimage.png)
        query_params = parse_qs(parsed.query)
        for param, value in query_params.items():
            for v in value:
                if re.match(r".*" + file_extensions, v.lower()):  # Check for image extensions in the query
                    return False
        
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise


# def tokenize(content):
#     soup = BeautifulSoup(content, "html.parser")
#     for script in soup(["script", "style", "meta"]):#factor out the text in these html tags
#         script.extract()

#     text = soup.get_text().lower()
#     tokens = re.findall(r'\b\w+\b', text)
#     return tokens

# def get_ics_subdomains(url):
#     global ics_subdomain_counter
#     global ics_subdomains
#     ics_subdomain_counter = 0
#     ics_subdomains = set()
#     parsed = urlparse(url)#parse url 
#     domain = parsed.netloc#get the domain of the url
#     ics_domain = ".ics.uci.edu"
#     if domain.endswith(ics_domain):
#         ics_subdomain_counter+=1
#         ics_subdomains.append(url)
    
# def get_unique_pages(url):
#     global unique_pages_counter
#     global domains_explored
#     unique_pages_counter = 0
#     domains_explored = set()
#     parsed = urlparse(url)
#     domain = parsed.netloc
#     if domain not in domains_explored:
#         unique_pages_counter+=1        
#     domains_explored.add(domain)#add to the set


# def get_word_count(content):
#     tokens = tokenize(content)
#     return len(tokens)#returns number of unique words/tokens

# def get_most_common_words(content):
#     tokens = tokenize(content)
#     stop_words = set("""a
# about
# above
# after
# again
# against
# all
# am
# an
# and
# any
# are
# aren't
# as
# at
# be
# because
# been
# before
# being
# below
# between
# both
# but
# by
# can't
# cannot
# could
# couldn't
# did
# didn't
# do
# does
# doesn't
# doing
# don't
# down
# during
# each
# few
# for
# from
# further
# had
# hadn't
# has
# hasn't
# have
# haven't
# having
# he
# he'd
# he'll
# he's
# her
# here
# here's
# hers
# herself
# him
# himself
# his
# how
# how's
# i
# i'd
# i'll
# i'm
# i've
# if
# in
# into
# is
# isn't
# it
# it's
# its
# itself
# let's
# me
# more
# most
# mustn't
# my
# myself
# no
# nor
# not
# of
# off
# on
# once
# only
# or
# other
# ought
# our
# ours	ourselves
# out
# over
# own
# same
# shan't
# she
# she'd
# she'll
# she's
# should
# shouldn't
# so
# some
# such
# than
# that
# that's
# the
# their
# theirs
# them
# themselves
# then
# there
# there's
# these
# they
# they'd
# they'll
# they're
# they've
# this
# those
# through
# to
# too
# under
# until
# up
# very
# was
# wasn't
# we
# we'd
# we'll
# we're
# we've
# were
# weren't
# what
# what's
# when
# when's
# where
# where's
# which
# while
# who
# who's
# whom
# why
# why's
# with
# won't
# would
# wouldn't
# you
# you'd
# you'll
# you're
# you've
# your
# yours
# yourself
# yourselves""".split()) #makes a list of the stop words
#     tokens_without_stops = [word for word in tokens if word not in stop_words]
#     freqs = Counter(tokens_without_stops)#gets the frequency of the words
#     top_50 = [word for word, freq in freqs.most_common(50)]     
#     return top_50
