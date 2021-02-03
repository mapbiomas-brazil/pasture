from flask import Blueprint, current_app, request, jsonify
from .model import Task
from .model import Config
import ee
from Lapig.Functions import type_process, login_gee
from dynaconf import settings
from sys import exit




login_gee(ee)


def id_(version,name):
    return f'{version}_{name}'


bp_config = Blueprint('config', __name__)

@bp_config.route('/generate_task_list', methods=['GET'])
def generate_task_list():
    try:
        for n,i in enumerate(settings.LISTA_CARTAS):
            rest = {
                    'version':settings.VERSION,
                    'name':str(i),
                    'state':type_process('None'),
                    'task_id':'None',
                    'num':n,
                }
            task = Task(id_=id_(
                rest['version'],
                rest['name']),
                **rest)
            task.save()
            #bp_config.logger.info(f'Add {task.json}')
        return jsonify({'state':'sucesso'}),201
    except Exception as e:
        return jsonify({'error': str(e) ,
                        'messagem':'Erro a gerar a lista'})
