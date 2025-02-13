from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker

class Crawler(object):
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.workers = list()
        self.worker_factory = worker_factory

    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        self.start_async()
        self.join()
        with open("output.txt", "w", encoding="utf-8") as file:
            for worker in self.workers:
                file.write(f"{len(worker.visited_urls)} unique pages found.\n")
                file.write(f"{worker.longest_page[0]} was the longest page with {worker.longest_page[1]} words.\n")
                file.write(f"Top 50 Words: {list(worker.word_counter.most_common(50))}\n")
                file.write(f"Found {len(worker.subdomains)} in ics.uci.edu: {worker.subdomains}\n")
            

    def join(self):
        for worker in self.workers:
            worker.join()
