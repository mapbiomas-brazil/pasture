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
        ERRORS = ERRORS + 1
        return in_queue,runnig
    except requests.exceptions.ConnectionError:
        logger.warning('Servidor Fora do ar')
        ERRORS = ERRORS + 1
        return in_queue,runnig

def check_tasks(ERRORS):
    try:
        g = get(f'http://{settings.SERVER}:{settings.PORT}/task/check')
        if g.status_code != 200:
            ERRORS = ERRORS + 1
    except json.decoder.JSONDecodeError:
        ERRORS = ERRORS + 1
    except requests.exceptions.ConnectionError:
        ERRORS = ERRORS + 1
