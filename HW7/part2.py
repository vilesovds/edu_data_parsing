"""
Написать программу, которая собирает «Хиты продаж» с сайтов техники М.видео, ОНЛАЙН ТРЕЙД и складывает данные в БД.
Магазины можно выбрать свои. Главный критерий выбора: динамически загружаемые товары.
"""

from driver_helper import get_driver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import By
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy_utils import URLType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
import json


FORMAT = '%(levelname)s:%(name)s:%(funcName)s:%(lineno)d: %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

Base = declarative_base()


class HitGood(Base):
    __tablename__ = 'hit_goods'
    id = Column(Integer, primary_key=True)
    shop = Column(String)
    url = Column(URLType)
    name = Column(String)
    vendor = Column(String)
    price = Column(Float)

    def __init__(self, shop, url, name, vendor, price):
        self.shop = shop
        self.url = url
        self.name = name
        self.vendor = vendor
        self.price = price

    def __init__(self, data: dict):
        self.update(data)

    def update(self, data: dict):
        self.shop = data.get('shop')
        self.url = data.get('url')
        self.name = data.get('name')
        self.vendor = data.get('vendor')
        self.price = data.get('price', 0.0)

    def __repr__(self):
        return f"<HitGood(\r\n\tshop: {self.shop}\r\n\tname: {self.name}\r\n\tvendor: {self.vendor}\r\n" \
               f"\tprice: {self.price}\r\n\turl: {self.url}\r\n)>"


def parse_mvideo(driver):
    base_url = "https://www.mvideo.ru"
    url = base_url + "?hits"

    def _get_data_from_good(good_item):
        res = {'shop': 'mvideo'}
        link = good_item.find_element_by_xpath('.//div[@class="fl-product-tile__description '
                                               'c-product-tile__description"]//h3/a')
        res['url'] = link.get_attribute("href")
        info = json.loads(link.get_attribute('data-product-info'))  # get additional product info
        logger.debug(info)
        res['name'] = info['productName']
        res['vendor'] = info['productVendorName']
        res['price'] = info['productPriceLocal']
        return res

    result = []
    gallery_xpath = '//div[@class="facelift gallery-layout products--shelve gallery-layout_products ' \
                    'gallery-layout_product-set grid-view"]'
    try:
        driver.get(url)
        # wanted container
        gallery = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, gallery_xpath))
        )
        hits_carousel = gallery.find_element_by_xpath('.//ul[@class="accessories-product-list"]')
        # scroll to element
        ActionChains(driver).move_to_element(hits_carousel).perform()
        # get counts of hits goods
        total_count = json.loads(hits_carousel.get_attribute("data-init-param"))['ajaxContentLoad']['total']
        logger.debug(f' total_count: {total_count}')
        # find button next
        next_btn = gallery.find_element_by_xpath('.//a[contains(@class, "next-btn")]')

        goods = hits_carousel.find_elements_by_tag_name('li')
        logger.debug(f"goods count: {len(goods)}")
        # waiting needed count of li elements
        while len(goods) < total_count:
            next_btn.click()
            driver.implicitly_wait(1)  # its help waiting render
            goods = hits_carousel.find_elements_by_tag_name('li')
            logger.debug(len(goods))

        result = [_get_data_from_good(good) for good in goods]
    except Exception as err:
        logger.error(err)
    return result


def parse_onlinetrade(driver):
    url = "https://www.onlinetrade.ru/"
    h2_hits_xpath = '//*[text()="Хиты продаж"]'

    def _parse_link(item_url):
        data = {'shop': 'onlinetrade', 'url': item_url}
        driver.open_in_new_tab(item_url)
        # product card
        card = driver.find_element_by_xpath('//div[@class="productPage__card"]')
        name = card.find_element_by_xpath('.//h1[@itemprop="name"]').text
        logger.debug(f'good name: {name}')
        data['name'] = name
        price = int(card.find_element_by_xpath('.//span[@itemprop="price"]').get_attribute('content'))
        logger.debug(f'price: {price}')
        data['price'] = price
        brand = card.find_element_by_xpath('.//div[@class="descr__techicalBrand__brandLink"]/a').text
        logger.debug(f'brand: {brand}')
        data['vendor'] = brand
        driver.close_but_index(0)  # close tabs but not root
        return data

    res = []
    try:
        driver.get(url)
        h2_hits = driver.find_element_by_xpath(h2_hits_xpath)
        container = h2_hits.find_element_by_xpath('../..')
        swiper_manage = container.find_element_by_xpath('.//div[@class="swiper__manage"]')

        swiper_container = container.find_element_by_xpath('.//div[contains(@class, "swiper-container")]')

        # go to elements
        ActionChains(driver).move_to_element(swiper_container).perform()

        bullets = swiper_manage.find_elements_by_xpath('.//span[contains(@class, "swiper-pagination-bullet")]')
        logger.debug(f'found {len(bullets)} bullet(s)\r\n')
        parsed_urls = []  # stack
        for bullet in bullets:
            # switch swiper
            bullet.click()
            # collect slides
            slides = swiper_container.find_elements_by_xpath('.//div[@class="swiper-slide indexGoods__item"]')
            logger.debug(f'found {len(slides)} slides\r\n')
            for slide in slides:
                link = slide.find_element_by_tag_name('a').get_attribute('href')
                if link not in parsed_urls:  # ignore already parsed
                    res.append(_parse_link(link))
                    parsed_urls.append(link)
    except Exception as err:
        logger.error(err)
    return res


def bd_save(data: list, engine):
    Session = sessionmaker(bind=engine)
    with Session() as session:
        for item in data:
            # url as uniq key. Update if found and add otherwise
            found = session.query(HitGood).filter(HitGood.url == item.get('url')).first()
            if found:
                found.update(item)
            else:
                session.add(HitGood(item))
        session.commit()


if __name__ == "__main__":
    # get environment settings
    driver = get_driver(os.environ.get('DRIVER_PATH'))
    engine = create_engine(os.environ.get('DATA_BASE'))

    # setup logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(ch)

    Base.metadata.create_all(engine)

    mv_data = parse_mvideo(driver)
    bd_save(mv_data, engine)
    ot_data = parse_onlinetrade(driver)
    bd_save(ot_data, engine)
    driver.close()
