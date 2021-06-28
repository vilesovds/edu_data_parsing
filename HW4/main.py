"""
Написать приложение, которое собирает основные новости с сайтов mail.ru, lenta.ru, yandex-новости.
Для парсинга использовать XPath. Структура данных должна содержать:
название источника;
наименование новости;
ссылку на новость;
дата публикации.
"""

from lxml import html
import requests
from datetime import datetime
import locale
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
FORMAT = '%(levelname)s:%(name)s:%(funcName)s:%(lineno)d: %(message)s'

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/91.0.4472.114 Safari/537.36'}
locale.setlocale(locale.LC_ALL, '')


@dataclass
class NewsItem:
    """Class for keeping news."""
    name: str
    link: str
    source: str
    date_time: datetime


def translate_from_dict(original_text, dictionary_of_translations):
    """
    Replace words by translation map
    :param original_text: str
    :param dictionary_of_translations: dict
    :return: str
    """
    out = original_text
    for target in dictionary_of_translations:
        out = out.replace(target, dictionary_of_translations[target])
    return out


def parse_lenta_ru():
    """
    Get top 10 news from lenta.ru
    :return: news list of dictionaries
    """
    month_map = {'января': 'Январь',
                 'февраля': 'Февраль',
                 'марта': 'Март',
                 'апреля': 'Апрель',
                 'мая': 'Май',
                 'июня': 'Июнь',
                 'июля': 'Июль',
                 'августа': 'Август',
                 'сентября': 'Сентябрь',
                 'октября': 'Октябрь',
                 'ноября': 'Ноябрь',
                 'декабря': 'Декабрь'
                 }

    base_url = 'https://lenta.ru/'
    news = []
    response = requests.get(base_url, headers=headers)
    root = html.fromstring(response.text)
    items = root.xpath("//section[contains(@class, 'b-top7-for-main')]//div[contains(@class,'item')]")
    for item in items:
        source = 'lena.tu'
        href = f"{base_url}{item.xpath('.//a/@href')[0]}"
        name = item.xpath('.//a[1]/text()')[0].replace('\xa0', ' ')
        date_time_str = item.xpath('.//a/time/@datetime')[0]
        date_time_str = translate_from_dict(date_time_str, month_map)
        datetime_object = datetime.strptime(date_time_str, ' %H:%M, %d %B %Y')
        ni = NewsItem(name, href, source, datetime_object)
        news.append(ni)
    return news


def parse_yandex_news():
    """
    Get main news from yandex.ru
    :return: news list of dictionaries
    """
    results = []
    base_url = 'https://yandex.ru/news'
    response = requests.get(base_url, headers=headers)
    root = html.fromstring(response.text)
    articles = root.xpath('//article')
    for article in articles:
        try:  # if not today news - could be an error
            name = article.xpath('.//a/h2/text()')[0].replace('\xa0', ' ')
            url = article.xpath('.//a/@href')[0]
            source = article.xpath('.//a/@aria-label')[0].replace('Источник: ', '')
            hours, minutes = article.xpath('.//span[@class="mg-card-source__time"]/text()')[0].split(':')
            datetime_object = datetime.today().replace(minute=int(minutes), hour=int(hours), microsecond=0)
            ni = NewsItem(name, url, source, datetime_object)
            results.append(ni)
        except Exception as err:
            logger.error(err)
    return results


def parse_mail_news():
    """
    Get 10 news from mail.ru
    :return: news list of dictionaries
    """
    def _parse_page(page_url):
        res = requests.get(page_url, headers=headers)
        page = html.fromstring(res.text)
        name = page.xpath('//h1/text()')[0].replace('\xa0', ' ')
        source = page.xpath('//span[@class="breadcrumbs__item"]//span[@class="link__text"]/text()')[0]
        date_time = page.xpath('//span[@class="breadcrumbs__item"]//span/@datetime')[0]
        datetime_object = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S%z')
        return NewsItem(name, page_url, source, datetime_object)

    results = []
    search_url = 'https://news.mail.ru/inregions/moscow/90/'
    response = requests.get(search_url, headers=headers)
    root = html.fromstring(response.text)
    articles = root.xpath('//div[@class="daynews__item"] | //ul[@data-module="TrackBlocks"]/li')

    for article in articles:
        url = article.xpath('.//a/@href')[0]
        results.append(_parse_page(url))
        time.sleep(1)
    return results


def main():
    import pandas as pd
    pd.set_option('display.max_columns', None)

    res = []
    lru = parse_lenta_ru()
    logger.debug(f'got {len(lru)} from lenta.ru')
    res.extend(lru)

    yn = parse_yandex_news()
    logger.debug(f'got {len(yn)} from yandex')
    res.extend(yn)

    mn = parse_mail_news()
    res.extend(mn)
    logger.debug(f'got {len(mn)} from mail.ru')

    pd = pd.DataFrame(res)
    print(pd.info)
    """
    DEBUG:__main__:main:142: got 10 from lenta.ru
    DEBUG:__main__:main:146: got 65 from yandex
    DEBUG:__main__:main:151: got 10 from mail.ru
    <bound method DataFrame.info of                                                  name  \
    0                     В метро Лондона произошел взрыв   
    1   Курский губернатор поручил силовикам «отработа...   
    2   Киев раскрыл сумму невыплаченных жителям Донба...   
    3   Белоруссия вышла из программы ЕС «Восточное па...   
    4   Таджикистан рассказал ОДКБ о нападении талибов...   
    ..                                                ...   
    80       В Москве снова закончилась вакцина «Ковивак»   
    81  Бесплатные автобусы КМ запустили из-за временн...   
    82  Диагностика вирусной пневмонии: в Москве начал...   
    83  Актриса Театра имени Моссовета Нина Коновалова...   
    84  Собянин рассказал о постепенном расширении вак...   
    
                                                 link  \
    0   https://lenta.ru//news/2021/06/28/london_sub/   
    1    https://lenta.ru//news/2021/06/28/zakomment/   
    2   https://lenta.ru//news/2021/06/28/donbass_ua/   
    3      https://lenta.ru//news/2021/06/28/vsyshli/   
    4         https://lenta.ru//news/2021/06/28/odkb/   
    ..                                            ...   
    80         https://news.mail.ru/society/46899946/   
    81         https://news.mail.ru/society/46903741/   
    82         https://news.mail.ru/society/46896201/   
    83         https://news.mail.ru/society/46900378/   
    84         https://news.mail.ru/society/46899454/   
    
                                                source                  date_time  
    0                                          lena.tu        2021-06-28 16:55:00  
    1                                          lena.tu        2021-06-28 16:57:00  
    2                                          lena.tu        2021-06-28 16:53:00  
    3                                          lena.tu        2021-06-28 16:51:00  
    4                                          lena.tu        2021-06-28 16:51:00  
    ..                                             ...                        ...  
    80                                            ТАСС  2021-06-28 11:46:10+03:00  
    81           Агентство городских новостей «Москва»  2021-06-28 16:56:12+03:00  
    82  Официальный портал Мэра и Правительства Москвы  2021-06-28 13:30:51+03:00  
    83           Агентство городских новостей «Москва»  2021-06-28 12:03:55+03:00  
    84                                          m24.ru  2021-06-28 12:42:27+03:00  
    
    [85 rows x 4 columns]>
    """


if __name__ == '__main__':
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(ch)
    main()
