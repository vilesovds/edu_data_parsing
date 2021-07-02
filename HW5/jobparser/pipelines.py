# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
import math


class JobparserPipeline(object):
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongobase = client.vacancies
        self.salaryparsers = {'sjru': self.sj_salary_parse, 'hhru': self.hh_salary_parse}

    def process_item(self, item, spider):
        collection = self.mongobase[spider.name]
        item['url'] = item['url'].split('?')[0]
        s_min, s_max, s_cur, s_type = self.salaryparsers[spider.name](''.join(item['salary']))
        item['salary_min'] = s_min
        item['salary_max'] = s_max
        item['salary_currency'] = s_cur
        item['salary_type'] = s_type
        item.pop('salary', None)
        collection.insert_one(item)
        return item

    def sj_salary_parse(self, salary: str):
        salary = salary.replace(u'\xa0', ' ')
        min_val = max_val = math.nan
        currency = cur_type = cur_time_period = 'none'
        if salary != 'По договорённости':
            cur_type = 'gross'
            lst = salary.split(' ')
            currency, cur_time_period = lst.pop().split('/')
            if lst[0] == 'от':
                min_val = ''.join(lst[1:])
            elif lst[0] == 'до':
                max_val = ''.join(lst[1:])
            else:
                if '—' in lst:
                    lst[lst.index('—')] = ' '
                    min_val, max_val = ''.join(lst).split(' ')
                else:
                    max_val = min_val = ''.join(lst)

        return float(min_val), float(max_val), currency, cur_type  # , cur_time_period

    def hh_salary_parse(self, salary: str):
        salary = salary.replace(u'\xa0', '')

        min_val = max_val = math.nan
        currency = cur_type = 'none'
        if salary != 'з/п не указана':
            lst = salary.split(' ')
            if lst[-1] == 'руки':
                cur_type = 'net'
                for _ in range(2):
                    lst.pop()
            else:
                cur_type = 'gross'
                for _ in range(3):
                    lst.pop()

            currency = lst.pop()
            if len(lst) == 4:
                min_val, max_val = lst[1], lst[3]
            elif lst[0] == 'от':
                min_val = lst[1]
            else:
                max_val = lst[1]
        return float(min_val), float(max_val), currency, cur_type

