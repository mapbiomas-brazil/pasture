from Sentinel.sentinel import get_Exports
from dynaconf import settings

from requests import post,get
from time import sleep
import json
from sys import exit
import requests
from random import randint

version = settings.VERSION
ERRORS = 0
MAXRUN = settings.QUANTITY_ALLOWED_IN_QUEUE

try:
    in_queue = get(f'http://{settings.SERVER}:{settings.PORT}/task/get').json()
    runnig = get(f'http://{settings.SERVER}:{settings.PORT}/task/runnig').json()
except json.decoder.JSONDecodeError:
    print('Servido não esta respondendo de forma correta')
    exit()
except requests.exceptions.ConnectionError:
    print('Servidor Fora do ar')
    exit(1)





while len(in_queue)+len(runnig) > 0:
    check_tasks(ERRROS)
    in_queue,runnig = get_info(in_queue,runnig,ERRROS)
    if len(runnig) < MAXRUN and len(in_queue) > 0:
        if len(in_queue) > 1:
            n = randint(0,len(in_queue))
        else:
            n = 0
        id_ = in_queue[n]['id_']
        name = in_queue[n]['name']
        num = in_queue[n]['num']
        task_id, res = get_Exports(version,num,name)
        runnig[id_] = task_id
        print(f'add task ID:{id_} gee_id:{task_id}')
        
    sleep(1)
    print(runnig)
    print(f'Errors = {ERRORS}')
    if ERRORS >=25:
        exit(1)
    
print('Finalizado')