"""
Написать программу, которая собирает входящие письма из своего или тестового почтового ящика,
и сложить информацию о письмах в базу данных (от кого, дата отправки, тема письма, текст письма).
"""
from driver_helper import get_driver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import By
import os
import logging

FORMAT = '%(levelname)s:%(name)s:%(funcName)s:%(lineno)d: %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def parse_mail(driver, login, password):
    url = 'https://mail.ru/'
    login_xpath = '//button[contains(@class, "ph-login")]'
    login_iframe_xpath = '//iframe[@class="ag-popup__frame__layout__iframe"]'
    layout_content_xpath = '//div[@class="layout__content-column"]'
    results = []

    def _login():
        login_btn = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, login_xpath))
        )
        logger.debug(login_btn.text)
        login_btn.click()
        # wait loading iframe
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, login_iframe_xpath))
        )

        form = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'form'))
        )
        # call 'other' input
        form.find_element_by_xpath('.//div[@data-test-id="other"]').click()
        user_name_input = form.find_element_by_xpath('.//input[@name="username"]')
        logger.debug(f'attempt to use login {login}')
        user_name_input.send_keys(login)
        form.find_element_by_xpath('.//button[@data-test-id="next-button"]').click()
        pass_input = form.find_element_by_xpath('.//input[@name="password"]')
        WebDriverWait(driver, 10).until(
            EC.visibility_of(pass_input)
        )
        pass_input.send_keys(password)
        form.find_element_by_xpath('.//button[@data-test-id="submit-button"]').click()
        # switch back
        driver.switch_to.default_content()

    def _parse_link(_url):
        ret = {}
        logger.debug(f'parsing {_url}')
        driver.open_in_new_tab(_url)
        # wait content
        layout_thread = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, ('//div[@class="layout__content"]')))
        )

        subject = layout_thread.find_element_by_xpath('.//h2[contains(@class, "thread__subject")]').text
        logger.debug(f' letter subject: {subject}')
        ret['subject'] = subject
        sender = layout_thread.find_element_by_xpath('.//span[@class="letter-contact"]')
        sender_name = sender.text
        sender_email = sender.get_attribute('title')
        logger.debug(f'sender: {sender_name} {sender_email}')
        ret['sender_name'] = sender_name
        ret['sender_email'] = sender_email
        date_str = layout_thread.find_element_by_xpath('.//div[@class="letter__date"]').text
        logger.debug(date_str)
        letter_body = layout_thread.find_element_by_xpath('.//div[@class="letter-body"]').text
        logger.debug(letter_body)
        ret['body_text'] = letter_body
        driver.close_but_index(0)
        return ret

    try:
        driver.get(url)
        _login()
        # now we can parsing
        layout = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, layout_content_xpath))
        )

        links = layout.find_elements_by_xpath(
            './/div[@class="dataset-letters"]//a[contains(@class, "llc") and contains(@class, "js-letter-list-item")]'
        )
        logger.debug(f'found {len(links)} links')
        for link in links:
            link_url = link.get_attribute('href')
            if not link_url:
                continue
            _parse_link(link_url)
    except Exception as err:
        logger.error(err)
    return results


if __name__ == "__main__":
    # setup logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(ch)

    driver = get_driver(os.environ.get('DRIVER_PATH'))
    login = os.environ.get('LOGIN')
    password = os.environ.get('PWD')

    parse_mail(driver, login, password)
    driver.close()
    driver.quit()
