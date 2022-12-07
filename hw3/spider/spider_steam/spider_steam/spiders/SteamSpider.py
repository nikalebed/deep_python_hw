import scrapy
from urllib.parse import urlencode
from urllib.parse import urljoin
import re
import json
from spider_steam.items import SpiderSteamItem


queries = ['гонки', 'симулятор', 'стратегии']


class SteamSpider(scrapy.Spider):
    name = 'SteamSpider'
    allowed_domains = ['store.steampowered.com']
    start_urls = ['http://store.steampowered.com/']

    def start_requests(self):
        for query in queries:
            for page in range(1, 3):
                url = 'https://store.steampowered.com/search/?' + urlencode(
                    {'term': query, 'page': page})
                yield scrapy.Request(url=url,
                                     callback=self.parse_keyword_response)

    def parse_keyword_response(self, response):
        game_urls = response.xpath(
            '//div[@id="search_resultsRows"]/a/@href').extract()
        for game_url in game_urls:
            yield scrapy.Request(url=game_url, callback=self.parse_game_page)

    def parse_game_page(self, response):
        items = SpiderSteamItem()
        name = response.xpath('//div[@id="appHubAppName"]/text()').extract()
        category = response.xpath(
            '//div[@class="blockbg"]/a//text()').extract()
        tags = response.xpath('//a[@class="app_tag"]/text()').extract()
        developers = response.xpath(
            '//div[@id="developers_list"]/a/text()').extract()
        release_date = response.xpath(
            '//div[@class="release_date"]/div[@class="date"]/text()').extract()
        price = response.xpath(
            '//div[@class ="game_purchase_price price"]/text()').extract()
        platforms = response.xpath(
            '//div[@class="game_area_purchase_platform"]/span/@class').extract()
        review_count = response.xpath(
            '//div[@class="summary column"]/meta[@itemprop="reviewCount"]/@content').extract()
        rating = response.xpath(
            '//div[@class="summary column"]/meta[@itemprop="ratingValue"]/@content').extract()

        items['name'] = ''.join(name).strip()
        items['category'] = ''.join(category).strip()
        items['tags'] = ', '.join(map(lambda x: x.strip(), tags)).strip()
        items['developers'] = ', '.join(
            map(lambda x: x.strip(), developers)).strip()
        items['release_date'] = ''.join(release_date).strip()
        items['price'] = ''.join(price[0]).strip()
        items['platforms'] = ', '.join(
            map(lambda x: x.strip().split()[-1], set(platforms))).strip()
        items['review_count'] = ''.join(review_count).strip()
        items['rating'] = ''.join(rating).strip()
        yield items
