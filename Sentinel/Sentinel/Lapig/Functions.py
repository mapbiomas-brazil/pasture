from dynaconf import settings
from pathlib import Path


def type_process(type_):
    if type_ in ['READY','RUNNING']:
        return 'RUNNING'
    if type_ == 'COMPLETED':
        return 'COMPLETED'
    if type_ == 'ERROR':
        return 'ERROR'
    return 'IN_QUEUE'
    
def error_in_task(__task):
    errors = [# Erros que nao poder rodar de novo
        'Image.classify: No valid training data were found.', 
        'Unable to write to bucket mapbiomas (permission denied).'
    ]
    try:
        if __task['error_message'] in errors:
            return 'ERROR'
        __task['state']
    except KeyError as e:
        return __task['state']
            


def id_(version,name):
    return f'{version}_{name}'

def login_gee(ee):
    try:
        ee.Initialize()
    except FileNotFoundError as e:
        __login_manual(ee)
    except ee.ee_exception.EEException as e:
        print('Login fall',e)
        __login_manual(ee)


def __login_manual(ee):
    ee.Authenticate()
    ee.Initialize()