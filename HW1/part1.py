"""
1. Посмотреть документацию к API GitHub,
разобраться как вывести список репозиториев для конкретного пользователя, сохранить JSON-вывод в файле *.json.
"""
import json
import requests
import os
import logging

FORMAT = '%(levelname)s:%(name)s:%(funcName)s:%(lineno)d: %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

endpoint = 'http://api.github.com'
headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {os.getenv("TOKEN")}'}


def user_repos(username: str):
    ret = {}
    parameters = {'name': username}
    req = requests.get(f'{endpoint}/users/{username}/repos', params=parameters, headers=headers)
    if req.status_code == 200:
        ret = req.json()
        logger.debug(f'user {username} have {len(ret)} repos')
    else:
        logger.error(f'error code {req.status_code}')
        raise(Exception(f'Bad response code : {req.status_code}'))
    return ret


if __name__ == '__main__':
    # setup logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(ch)

    user = 'vilesovds'
    # get and save results to file
    with open('results.json', 'w') as f:
        json.dump(user_repos(user), f,  indent=4)
