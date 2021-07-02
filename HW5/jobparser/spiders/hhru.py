# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from jobparser.items import JobparserItem


class HhruSpider(scrapy.Spider):
    name = 'hhru'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?area=&fromSearchLine=true&st=searchVacancy&text=python']

    def parse(self, response: HtmlResponse):
        next_page = response.xpath('//a[@data-qa="pager-next"]/@href').extract_first()
        yield response.follow(next_page, callback=self.parse)
        vacancies = response.xpath('//a[@data-qa="vacancy-serp__vacancy-title"]/@href').extract()
        for link in vacancies:
            yield response.follow(link, callback=self.vacancy_parse)

    def vacancy_parse(self, response: HtmlResponse):
        name = response.css('div.vacancy-title h1.bloko-header-1::text').extract_first()
        salary = response.xpath('//p[@class="vacancy-salary"]/span/text()').extract()
        yield JobparserItem(name=name, salary=salary)
