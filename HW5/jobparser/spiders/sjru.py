# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from jobparser.items import JobparserItem


class SjruSpider(scrapy.Spider):
    name = 'sjru'
    allowed_domains = ['superjob.ru']
    start_urls = ['https://www.superjob.ru/vacancy/search/?keywords=python']

    def parse(self, response: HtmlResponse):
        next_page = response.xpath('//a[contains(@class, "f-test-button-dalshe")]/@href').extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        links = response.xpath('//div[contains(@class,"f-test-vacancy-item")]/descendant::a[1]/@href').extract()
        for link in links:
            if link:
                yield response.follow(link, callback=self.vacancy_parse)

    def vacancy_parse(self, response: HtmlResponse):
        name = response.css('h1::text').extract_first()
        salary = response.xpath('//h1/../span/descendant::*/text()').extract()
        url = response.url
        yield JobparserItem(name=name, salary=salary, url=url)
