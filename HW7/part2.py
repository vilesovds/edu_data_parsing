"""
Написать программу, которая собирает «Хиты продаж» с сайтов техники М.видео, ОНЛАЙН ТРЕЙД и складывает данные в БД.
Магазины можно выбрать свои. Главный критерий выбора: динамически загружаемые товары.
"""

from driver_helper import get_driver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import By
from selenium.webdriver.support import expected_conditions as EC
import os
import logging
import json

import io
from PIL import Image

FORMAT = '%(levelname)s:%(name)s:%(funcName)s:%(lineno)d: %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(ch)


def parse_mvideo(driver):
    url = "https://www.mvideo.ru/?hits"

    def _get_data_from_good(good_item):
        res = {}
        link = good_item.find_element_by_xpath('.//div[@class="fl-product-tile__description '
                                               'c-product-tile__description"]//h3/a')
        res['url'] = url + link.get_attribute("href")
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
        gallery = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, gallery_xpath))
        )
        hits_carousel = gallery.find_element_by_xpath('.//ul[@class="accessories-product-list"]')
        ActionChains(driver).move_to_element(hits_carousel).perform()
        # get counts of hits goods
        total_count = json.loads(hits_carousel.get_attribute("data-init-param"))['ajaxContentLoad']['total']
        logger.debug(f' total_count: {total_count}')
        # find button next
        # next_btn = gallery.find_element_by_xpath('.//a[contains(@class, "next-btn")]')

        goods = hits_carousel.find_elements_by_tag_name('li')
        logger.debug(len(goods))
        while len(goods) < total_count:
            next_btn = gallery.find_element_by_xpath('.//a[contains(@class, "next-btn")]')
            ActionChains(driver).move_to_element(next_btn).perform()
            logger.debug(next_btn.is_displayed())
            next_btn.click()
            goods = hits_carousel.find_elements_by_tag_name('li')
            logger.debug(len(goods))

        result = [_get_data_from_good(good) for good in goods]
    except Exception as err:
        logger.error(err)

    return result


def parse_onlinetrade(driver):
    url = "https://www.onlinetrade.ru/"
    driver.get(url)
    return driver.current_url


def bd_save(data: list):
    print(data)


if __name__ == "__main__":
    driver = get_driver(os.environ.get('DRIVER_PATH'))
    mv_data = parse_mvideo(driver)
    bd_save(mv_data)
    # ot_data = parse_onlinetrade(driver)
    # bd_save(ot_data)
    driver.close()
