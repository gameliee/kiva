from random import randint
from pathlib import Path
import json
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


ENDPOINT = "https://api.kivaws.org/graphql"

query_file = Path(__file__).parent / "fetch_loans.graphql"
with open(query_file) as f:
    QUERY = f.read()


class MyCrawlGraphQlSpider(CrawlSpider):
    name = "kiva"
    start_urls = [ENDPOINT]  # Replace with your API URL

    custom_settings = {
        "FEEDS": {
            "./data/kiva_%(time)s.jsonl": {"format": "jsonl", "encoding": "utf8"},
            # "fundingvn_%(time)s.marshall": {"format": "marshal"},
        },
        # 'DUPEFILTER_CLASS': RFPDupeFilter,
        "AUTOTHROTTLE_ENABLED": True,
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "scrapy.log",
    }

    rules = (Rule(LinkExtractor(), callback="parse_response", follow=True),)

    def start_requests(self):
        # Define initial values for offset and limit
        # We can take advantage of this to increase the request number
        self.NUMOFFSET = 32

        limit = 200
        for i in range(self.NUMOFFSET):
            offset = i * limit

            # Create a JSON object with the query and variables
            request_data = {"query": QUERY, "variables": {"offset": offset, "limit": limit}}

            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps(request_data),
                callback=self.parse_response,
                meta={"offset": offset, "limit": limit},
            )

    def parse_response(self, response):
        data = json.loads(response.text)

        loans = data.get("data", {}).get("lend", {}).get("loans", {}).get("values", [])
        for loan in loans:
            yield {"loan": loan}  # Yield Scrapy items

        # Perform pagination by incrementing the offset and making a new request
        offset = response.meta["offset"] + response.meta["limit"] * self.NUMOFFSET
        limit = response.meta["limit"]

        if loans:
            request_data = {"query": QUERY, "variables": {"offset": offset, "limit": limit}}
            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps(request_data),
                callback=self.parse_response,
                meta={"offset": offset, "limit": limit},
            )


if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess()
    process.crawl(MyCrawlGraphQlSpider)
    process.start()
