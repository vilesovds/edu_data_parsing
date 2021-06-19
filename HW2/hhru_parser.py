from common import headers
from async_run import async_run
import asyncio
import aiohttp
import math
from bs4 import BeautifulSoup as bs


def hh_salary_parse(salary: str):
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


def hh_bs_parse_dom(content):
    res = {}
    dom = bs(content, 'html.parser')
    title = dom.find('div', {'class': 'vacancy-title'})
    res['name'] = title.findChildren()[0].get_text()

    res['salary_min'], res['salary_max'], res['salary_currency'], res['salary_type'] = hh_salary_parse(
        title.findChildren()[1].get_text()
    )
    company_name = dom.find('a', {'class': 'vacancy-company-name'})
    if company_name:
        filtered_text = company_name.get_text().replace(u'\xa0', ' ')
        res['company_name'] = filtered_text
    return res


async def parse_vacancy(session, url):
    results = {}
    async with session.get(url) as resp:
        content = await resp.text()
        results = await async_run(hh_bs_parse_dom, content)
        results['url'] = str(resp.url).split('?')[0]
        results['site'] = 'hh.ru'

    return results


async def parse_page(session, url, params):
    async with session.get(url, params=params) as resp:
        content = await resp.text()
        a_tags = bs(content, 'html.parser').find_all('a', {'class': 'bloko-link',
                                                     'data-qa': 'vacancy-serp__vacancy-title'})
        return [tag['href'] for tag in a_tags]


async def hh_search_and_parse(search_query, pages=10):
    """
    Search job offers on sites, parse and save to DB
    :param search_query: string
    :param pages: int, maximum number of pages
    """
    search_url = "https://hh.ru/search/vacancy"
    params = {'text': search_query}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(search_url, params=params) as resp:
            params = range(0, pages)
            urls = await asyncio.gather(*[parse_page(session, resp.url, {'page': param}) for param in params],
                                        return_exceptions=True)
            res = await asyncio.gather(*[parse_vacancy(session, url) for x in urls for url in x],
                                       return_exceptions=True)
            return res
