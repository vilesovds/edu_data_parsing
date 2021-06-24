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
from superjonru_parser import sj_search_and_parse
import asyncio
from pprint import pprint


superjob_url = "https://www.superjob.ru/"


if __name__ == "__main__":
    import pandas as pd


    async def main(search_query, pages=10):
        pd.set_option('display.max_columns', None)

        res_sj = await sj_search_and_parse(search_query, pages, 5)
        frame_sj = pd.DataFrame(res_sj)
        print(frame_sj.head())
        frame_sj.to_csv(f'sj_res_{search_query}.csv')

        res = await hh_search_and_parse(search_query, pages, 5)

        frame_hh = pd.DataFrame(res)
        print(frame_hh.head())
        frame_hh.to_csv(f'hh_res_{search_query}.csv')

        res_frame = pd.concat([frame_sj, frame_hh], ignore_index=True)
        res_frame.to_csv(f'all_res_{search_query}.csv')


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main('инженер', 10))
