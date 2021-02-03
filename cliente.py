from Sentinel.sentinel import get_Exports
from loguru import logger

from requests import post,get
from time import sleep
from dynaconf import settings
from os import environ 
import json
from sys import exit
import requests
from random import randint

version = settings.VERSION
ERRORS = 0
MAXRUN = settings.QUANTITY_ALLOWED_IN_QUEUE



#logger.add(stderr, format="{time} {level} {message}", level="DEBUG")
logger.debug("That's it, beautiful and simple logging!")
logger.add("client.log",format="{time} [{level}] {name}:{module}:[{file}:{line}] {message} | {exception} ", rotation="500 MB",level='WARNING') 


try:
    in_queue = get(f'http://{settings.SERVER}:{settings.PORT}/task/get').json()
    runnig = get(f'http://{settings.SERVER}:{settings.PORT}/task/runnig').json()
except json.decoder.JSONDecodeError:
    logger.warning('Servido não esta respondendo de forma correta')
    exit()
except requests.exceptions.ConnectionError:
    logger.warning('Servidor Fora do ar')
    exit(1)

def get_info(in_queue,runnig):
    global ERRORS
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

def check_tasks():
    global ERRORS
    try:
        g = get(f'http://{settings.SERVER}:{settings.PORT}/task/check')
        if g.status_code != 200:
            ERRORS = ERRORS + 1
    except json.decoder.JSONDecodeError:
        ERRORS = ERRORS + 1
    except requests.exceptions.ConnectionError:
        ERRORS = ERRORS + 1



while len(in_queue)+len(runnig) > 0:
    check_tasks()
    in_queue,runnig = get_info(in_queue,runnig)
    if len(runnig) < MAXRUN and len(in_queue) > 0:
        if len(in_queue) > 1:
            n = randint(0,len(in_queue)-1)
        else:
            n = 0
        try:
            id_ = in_queue[n]['id_']
            name = in_queue[n]['name']
            num = in_queue[n]['num']
            task_id, res = get_Exports(version,num,name)
            runnig[id_] = task_id
            logger.info(f'add task ID:{id_} gee_id:{task_id}')
        except Exception as e:
            logger.warning(f'n:{n}, tamanho:len(in_queue), fila:{in_queue}, error:{e}')
        
        
    sleep(1)
    logger.info(f'Estamos processando {len(runnig)}')
    logger.info(f'Errors = {ERRORS}')
    if ERRORS >=25:
        exit(1)
    
logger.info('Finalizado')