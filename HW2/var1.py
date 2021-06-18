"""
Необходимо собрать информацию о вакансиях на вводимую должность (используем input или через аргументы) с сайтов
Superjob и HH. Приложение должно анализировать несколько страниц сайта (также вводим через input или аргументы).
Получившийся список должен содержать в себе минимум:
- Наименование вакансии.
- Предлагаемую зарплату (отдельно минимальную и максимальную).
- Ссылку на саму вакансию.
- Сайт, откуда собрана вакансия.
### По желанию можно добавить
ещё параметры вакансии (например, работодателя и расположение).
Структура должна быть одинаковая для вакансий с обоих сайтов.
Общий результат можно вывести с помощью dataFrame через pandas.
"""
import math

from bs4 import BeautifulSoup as bs
import asyncio
import aiohttp
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pprint import pprint

# executor = ProcessPoolExecutor(max_workers=4)
executor = ProcessPoolExecutor()

superjob_url = "https://www.superjob.ru/"


async def async_run(task_func, *args):
    """
    Run task in executor as async coroutine
    :param task_func: name of function
    :param args: arguments
    :return function call results
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor,
        partial(task_func, *args)
    )


class BaseParser:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/91.0.4472.106 Safari/537.36'}
    search_url = 'http://example.com'


class HHruParser(BaseParser):
    def __init__(self):
        self.session = None
        self.search_url = "https://hh.ru/search/vacancy"

    async def _parse_page(self, url, params):
        async with self.session.get(url, params=params) as resp:
            content = await resp.text()
            a_tags = bs(content, 'html.parser').find_all('a', {'class': 'bloko-link',
                                                               'data-qa': 'vacancy-serp__vacancy-title'})
            return [tag['href'] for tag in a_tags]

    @classmethod
    def salary_parse(cls, salary: str):
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

    def _bs_parse_dom(self, content):
        res = {}
        dom = bs(content, 'html.parser')
        title = dom.find('div', {'class': 'vacancy-title'})
        res['name'] = title.findChildren()[0].get_text()

        res['salary_min'], res['salary_max'], res['salary_currency'], res['salary_type'] = self._salary_parse(
            title.findChildren()[1].get_text()
        )
        return res

    async def _parse_vacancy(self, url):
        results = {}
        async with self.session.get(url) as resp:
            content = await resp.text()
            results = await async_run(self._bs_parse_dom, content)
            results['url'] = str(resp.url).split('?')[0]
        return results

    async def search_and_parse(self, search_query, pages=10):
        """
        Search job offers on sites, parse and save to DB
        :param search_query: string
        :param pages: int, maximum number of pages
        """
        params = {'text': search_query}
        self.session = aiohttp.ClientSession(headers=self.headers)
        async with self.session as session:
            async with session.get(self.search_url, params=params) as resp:
                params = range(0, pages)
                urls_lists = await asyncio.gather(*[self._parse_page(resp.url, {'page': param}) for param in params],
                                                  return_exceptions=True)
                res = await asyncio.gather(*[self._parse_vacancy(url) for x in urls_lists for url in x],
                                           return_exceptions=False)
                return res


async def main(search_query, pages=10):
    hh_parser = HHruParser()
    res = await hh_parser.search_and_parse(search_query, pages)
    print(f'found {len(res)} items')
    pprint(res)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main('Уборщица', 10))
