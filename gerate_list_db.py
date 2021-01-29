from dynaconf import settings
from requests import get, post
from Lapig.Functions import type_process


if __name__ == '__main__':
        

    for n,i in enumerate(settings.LISTA_CARTAS):
        rest = {
                'version':settings.VERSION,
                'name':str(i),
                'state':type_process('None'),
                'task_id':'None',
                'num':n,
            }
        p=post(f'http://{settings.SERVER}:{settings.PORT}/add',json= rest)
        print(p.text)
        print(rest)

