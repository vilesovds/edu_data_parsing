"""
1. Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию, записывающую собранные
 вакансии в созданную БД.
2. Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой больше введённой суммы.
3. Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта.
"""
from superjobru_parser import sj_search_and_parse
from hhru_parser import hh_search_and_parse
from pymongo import MongoClient
import argparse
import asyncio
from pprint import pprint

client = MongoClient('localhost', 27017)
db = client['vacancies']


def update(query: str, pages: int):
    """
    Parse hh.ru and superjob.ru by search query and update that information in database
    """
    loop = asyncio.get_event_loop()
    res_sj = loop.run_until_complete(sj_search_and_parse(query, pages, 5))
    res_hh = loop.run_until_complete(hh_search_and_parse(query, pages, 5))

    hh = db.hh
    for item in res_hh:
        hh.update_one({'_id': item['url']}, {'$set': item}, upsert=True)
    sj = db.sj
    for item in res_sj:
        sj.update_one({'_id': item['url']}, {'$set': item}, upsert=True)


def search(query: float):
    """
    Search vacancy in database with salary more than query
    TODO currency conversion
    """
    result = []
    print(query)
    result.extend(
        db.hh.find({'$or': [{'salary_min': {'$gt': query}}, {'salary_max': {'$gt': query}}]
                    }, {'_id': 0, 'site': 0})
    )
    result.extend(
        db.sj.find({'$or': [{'salary_min': {'$gt': query}}, {'salary_max': {'$gt': query}}]
                    }, {'_id': 0, 'site': 0})
    )
    return result


def main():
    parser = argparse.ArgumentParser(description='Working with vacancies')
    subparsers = parser.add_subparsers(dest='function')
    parser_update = subparsers.add_parser('update', help='update database by vacancies by search result with keywords')
    parser_update.add_argument('--pages', nargs=1, type=int, default=10)
    parser_update.add_argument('update_query', nargs='+')

    parser_search = subparsers.add_parser('search')
    parser_search.add_argument('search_query', nargs=1, type=float, help='query for search')

    args = parser.parse_args()
    if args.function == 'update':
        update(''.join(args.update_query), args.pages[0])
    elif args.function == 'search':
        res = search(args.search_query[0])
        pprint(res)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
