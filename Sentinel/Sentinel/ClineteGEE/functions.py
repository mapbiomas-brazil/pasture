from dynaconf import settings
from loguru import logger

import json
import requests
from requests import get

def get_info(in_queue,runnig,ERRORS):
    try:
        in_queue = get(f'http://{settings.SERVER}:{settings.PORT}/task/get').json()
        runnig = get(f'http://{settings.SERVER}:{settings.PORT}/task/runnig').json()
        return in_queue,runnig
    except json.decoder.JSONDecodeError:
        ERRORS.add()
        return in_queue,runnig
    except requests.exceptions.ConnectionError:
        logger.warning('Servidor Fora do ar')
        ERRORS.add()
        return in_queue,runnig

def check_tasks(ERRORS):
    try:
        g = get(f'http://{settings.SERVER}:{settings.PORT}/task/check')
        if g.status_code != 200:
            ERRORS.add()
    except json.decoder.JSONDecodeError:
        ERRORS.add()
    except requests.exceptions.ConnectionError:
        ERRORS.add()


class Error():
    def __init__(self):
        self.error = 0
    
    def get(self):
        return self.error

    def add(self):
        self.error = self.error+1
