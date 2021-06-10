"""
Написать программу, которая собирает входящие письма из своего или тестового почтового ящика,
и сложить информацию о письмах в базу данных (от кого, дата отправки, тема письма, текст письма).
"""
from driver_helper import get_driver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import By
from sqlalchemy import create_engine, Column, Integer, Text, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import EmailType

import os
import logging

FORMAT = '%(levelname)s:%(name)s:%(funcName)s:%(lineno)d: %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

Base = declarative_base()


class Email(Base):
    __tablename__ = 'letters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String)
    sender_email = Column(EmailType)
    sender_name = Column(String)
    date = Column(String)
    body_text = Column(Text)

    def __init__(self, subject, email, name, text, date):
        self.subject = subject
        self.sender_email = email
        self.sender_name = name
        self.body_text = text
        self.date = date

    def __init__(self, data: dict):
        self.update(data)

    def update(self, data: dict):
        self.subject = data.get('subject')
        self.sender_email = data.get('sender_email')
        self.sender_name = data.get('sender_name')
        self.body_text = data.get('body_text')
        self.date = data.get('date')

    def __eq__(self, other):
        return self.subject == other.subject and self.date == other.date \
               and self.sender_email == other.sender_email and self.body_text == other.body_text

    def __repr__(self):
        return f"<Email(\r\n\tsubject: {self.subject}\r\n\tsender_name: {self.sender_name}\r\n" \
               f"\tsender_email: {self.sender_email}\r\n\tdate: {self.date}\r\n" \
               f"\tbody: {self.body_text}\r\n)>"


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
        ret['date'] = date_str
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
            results.append(_parse_link(link_url))
    except Exception as err:
        logger.error(err)
    return results


def bd_save(data: list, engine):
    Session = sessionmaker(bind=engine)
    with Session() as session:
        for item in data:
            # compare
            founds = session.query(Email).filter(Email.subject.like(item.get('subject')),
                                                 Email.sender_email.like(item.get('sender_email'))).all()
            the_same = False
            if founds:
                for found in founds:
                    if found == Email(item):
                        logger.debug(f'latter was already added\r\n')
                        the_same = True
                        break
            if not the_same:
                session.add(Email(item))
        session.commit()


if __name__ == "__main__":
    # setup logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(ch)

    driver = get_driver(os.environ.get('DRIVER_PATH'))
    login = os.environ.get('LOGIN')
    password = os.environ.get('PWD')

    engine = create_engine(os.environ.get('DATA_BASE'))
    Base.metadata.create_all(engine)

    data = parse_mail(driver, login, password)
    if len(data):
        bd_save(data, engine)
    driver.close()
    driver.quit()
