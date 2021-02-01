from flask import Blueprint, current_app, request, jsonify
from .model import Task
import ee
from Lapig.Functions import type_process, login_gee
from dynaconf import settings
from sys import exit



login_gee(ee)


bp_task = Blueprint('task', __name__)


def id_(version,name):
    return f'{version}_{name}'




@bp_task.route('/get', methods=['GET'])
def get_tasks():
    task = Task.objects(state='IN_QUEUE').all()
    if not task:
        return jsonify([])
    else:
        return task.to_json(),200, {'ContentType':'application/json'} 

@bp_task.route('/runnig', methods=['GET'])
def get_runnig():
    task = Task.objects(
        version = settings.VERSION,
        state='RUNNING').all()
    if not task:
        return jsonify({})
    else:
        runnig = {}
        for i in task:
            runnig[i.id_] = i.task_id
        return runnig,200, {'ContentType':'application/json'} 




@bp_task.route('/state/<string:id>', methods=['GET'])
def get_state(id):
    task = Task.objects(id_=id).first()
    if not task:
        return jsonify([])
    else:
        return task.to_json(),200, {'ContentType':'application/json'} 


@bp_task.route('/update', methods=['POST'])
def update_record():
    record = request.json
    print(record)
    task = Task.objects(id_=record['id_']).first()
    if not task:
        return jsonify({'error': 'data not found'})
    else:
        state = record['state']
        task_id = record['task_id']
        task.update(
            state = state,
            task_id = task_id)
        bp_task.logger.info(f'Update na Task: {task_id}')
    return task.to_json()


@bp_task.route('/add', methods=['POST'])
def add():
    record = request.json
    # {'version': 'V001', 'name': '2019', 'state': 'None', 'task_id': 'None'}
    task = Task(id_=id_(
        record['version'],
        record['name']),
        **record)
    task.save()
    return jsonify(task.to_json())


@bp_task.route('/check', methods=['GET', 'POST'])
def check_tasks():
    tasks = Task.objects(
        version = settings.VERSION,
        state__ne = 'COMPLETED',
        task_id__ne = 'None').all()
    queue = []
    for i in tasks:
        state = ee.batch.Task(i.task_id,'','').status()['state']
        i.update(state=type_process(state))
        queue.append(i.to_json())
        
    return jsonify(queue)