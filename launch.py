from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler


def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    crawler.start()
    print(f"{len(crawler.visited_urls)} unique pages found.")
    print(f"{crawler.longest_page[0]} was the longest page with {crawler.longest_page[1]} words.")
    print(f"Top 50 Words: {list(crawler.word_counter.most_common(50))}")
    print(f"Found {len(crawler.subdomains)} in ics.uci.edu: {crawler.subdomains}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)
