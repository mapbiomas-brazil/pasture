from dynaconf import settings
from pathlib import Path


def type_process(type_):
    if type_ in ['READY','RUNNING']:
        return 'RUNNING'
    if type_ == 'COMPLETED':
        return 'COMPLETED'
    return 'IN_QUEUE'
    

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