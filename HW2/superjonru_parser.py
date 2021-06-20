from common import headers
from async_run import async_run
import asyncio
import aiohttp
import math
from bs4 import BeautifulSoup as bs


def sj_salary_parse(salary: str):
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

    return float(min_val), float(max_val), currency, cur_type, cur_time_period


def bs_parse_dom(content):
    res = {}
    dom = bs(content, 'html.parser')
    title = dom.find('h1')
    res['name'] = title.get_text()

    res['salary_min'], res['salary_max'], res['salary_currency'], res['salary_type'], res['salary_period'] = \
        sj_salary_parse(dom.find('span', {'class': '_1OuF_ ZON4b'}).get_text())
    company_name = dom.find('h2', {'class': '_1h3Zg _2rfUm _2hCDz _2ZsgW _21a7u _2SvHc'})
    if company_name:
        res['company_name'] = company_name.get_text()
    return res


async def parse_vacancy(session, url):
    results = {}
    try:
        async with session.get(url) as resp:
            content = await resp.text()
            results = await async_run(bs_parse_dom, content)
            results['url'] = str(resp.url).split('?')[0]
            results['site'] = 'superjob.ru'
    except Exception as err:
        print(f'error: {err}')
    return results


async def parse_page(session, url, params):
    urls = []
    try:
        async with session.get(url, params=params) as resp:
            content = await resp.text()
            items = bs(content, 'html.parser').find_all('div', {'class': "f-test-search-result-item"})
            for item in items:
                a_tag = item.find('a')
                if a_tag and a_tag['href'].startswith('/vakansii'):
                    urls.append('https://www.superjob.ru' + a_tag['href'])
    except Exception as err:
        print(f'error: {err}')
    return urls


async def sj_search_and_parse(search_query, pages=10, connections_limit=0):
    """
    Search job offers on sites, parse and save to DB
    :param search_query: string
    :param pages: int, maximum number of pages
    :param connections_limit: limit connections if needed
    """
    search_url = "https://www.superjob.ru/vacancy/search/"
    params = {'keywords': search_query}
    try:
        conn = aiohttp.TCPConnector(limit=connections_limit)
        async with aiohttp.ClientSession(headers=headers, connector=conn) as session:
            async with session.get(search_url, params=params) as resp:
                params = range(1, pages)
                await resp.read()
                urls = await asyncio.gather(*[parse_page(session, resp.url, {'page': param}) for param in params],
                                            return_exceptions=False)

                res = await asyncio.gather(*[parse_vacancy(session, url) for x in urls for url in x if url],
                                           return_exceptions=False)
                return res
    except Exception as err:
        print(f'error : {err}')

if __name__ == "__main__":
    from pprint import pprint


    async def main(search_query, pages=10):
        res = await sj_search_and_parse(search_query, pages)
        print(f'found {len(res)} items')
        pprint(res)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main('Уборщик в ресторан', 10))
