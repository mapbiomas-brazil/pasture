from Sentinel.sentinel import get_Exports
from loguru import logger
from ClineteGEE.functions import get_info, check_tasks
from requests import post,get
from time import sleep
from dynaconf import settings
from os import environ 
import json
from sys import exit
import requests
from random import choice




def main():
    version = settings.VERSION
    ERRORS = 0
    MAXRUN = settings.QUANTITY_ALLOWED_IN_QUEUE
    try:
        in_queue = get(f'http://{settings.SERVER}:{settings.PORT}/task/get').json()
        runnig = get(f'http://{settings.SERVER}:{settings.PORT}/task/runnig').json()
    except json.decoder.JSONDecodeError:
        logger.warning('Servido não esta respondendo de forma correta')
        exit()
    except requests.exceptions.ConnectionError:
        logger.warning('Servidor Fora do ar')
        exit(1)


    while len(in_queue)+len(runnig) > 0:
        check_tasks(ERRORS)
        in_queue,runnig = get_info(in_queue,runnig,ERRORS)
        if len(runnig) < MAXRUN and len(in_queue) > 0:
            element = choice(in_queue)
            try:
                id_ = element['id_']
                name = element['name']
                num = element['num']
                task_id, res = get_Exports(version,num,name)
                runnig[id_] = task_id
                logger.info(f'add task ID:{id_} gee_id:{task_id}')
            except Exception as e:
                logger.warning(f'element:{element}, tamanho:len(in_queue), fila:{in_queue}, error:{e}')
            
            
        sleep(1)
        logger.info(f'Estamos processando {len(runnig)}')
        logger.info(f'Errors = {ERRORS}')
        if ERRORS >=25:
            exit(1)
        
    logger.info('Finalizado')