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
from hhru_parser import hh_search_and_parse

import asyncio
from pprint import pprint


superjob_url = "https://www.superjob.ru/"


async def main(search_query, pages=10):
    res = await hh_search_and_parse(search_query, pages)
    print(f'found {len(res)} items')
    pprint(res)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main('Инженер', 10))
