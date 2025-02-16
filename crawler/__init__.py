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
        with open("1.txt", "w", encoding="utf-8") as file:
            file.write(f"{len(self.workers[0].visited_urls)} unique urls\n")
            file.write(f"{self.workers[0].visited_urls}\n")
        with open("2.txt", "w", encoding="utf-8") as file:
            file.write(f"{self.workers[0].longest_page}\n")
        with open("3.txt", "w", encoding="utf-8") as file:
            file.write(f"{self.workers[0].word_counter}\n")
        with open("4.txt", "w", encoding="utf-8") as file:
            try: # in case i made an error
                sorted_subdomains = sorted(self.workers[0].subdomains.keys())
                for subdomain in sorted_subdomains:
                    file.write(f"{subdomain}, {self.workers[0].subdomains[subdomain]}\n")
            except:
                pass
            file.write(f"{self.workers[0].subdomains}\n")

    def join(self):
        for worker in self.workers:
            worker.join()
