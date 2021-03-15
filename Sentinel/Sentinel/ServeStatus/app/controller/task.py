from flask import Blueprint, current_app, request, jsonify
from ServeStatus.app.model import Task
import ee
from Lapig.Functions import type_process, login_gee, error_in_task, id_
from dynaconf import settings
from sys import exit
import urllib3


login_gee(ee)
bp_task = Blueprint('task', __name__,url_prefix='/task')


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
        runnig = {i.id_:i.task_id for i in task}
        return runnig,200, {'ContentType':'application/json'} 

@bp_task.route('/completed', methods=['GET'])
def get_completed():#completed
    task = Task.objects(
        version = settings.VERSION,
        state='COMPLETED').all()
    error = Task.objects(
        version = settings.VERSION,
        state='ERROR').all()
    len_error = len(error)
    if not error:
        len_error = 0
        error = {}
    else:
        error = {i.id_:i.task_id for i in error}
    if not task:
        return jsonify([{'len':0, 'falta':len(settings.LIST_OF_TASKS)},{'task':{}}])
    else:
        completed = {i.id_:i.task_id for i in task}
        tamanho=len(completed)
        return jsonify([{
            'completed':tamanho,
            'errors': len_error,
            'falta':(len(settings.LIST_OF_TASKS) - (tamanho+len_error))
            },{
                'task_ok':completed,
                'task_error': error
        }]) ,200, {'ContentType':'application/json'} 


@bp_task.route('/errors', methods=['GET'])
def get_errors():#errors
    task = Task.objects(
        version = settings.VERSION,
        state='ERROR').all()
    if not task:
        return jsonify([{'len':0},{'task':{}}])
        
    else:
        errors = {i.id_:i.task_id for i in task}
        tamanho=len(errors)
        return jsonify([{'len':tamanho,'falta':(len(settings.LIST_OF_TASKS) - tamanho)},{'task':errors}]) ,200, {'ContentType':'application/json'} 





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
    # print(record)
    task = Task.objects(id_=record['id_']).first()
    if not task:
        return jsonify({'error': 'data not found'})
    else:
        state = record['state']
        task_id = record['task_id']
        task.update(
            state = state,
            task_id = task_id)
        current_app.logger.warning(f'Update na Task: {task_id}')
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
        task_id__ne = 'None').filter(state__ne='COMPLETED').filter(state__ne='ERROR').all()
    queue = []
    tasks_in_queue ={i.task_id:i for i in tasks}
    try:
        all_task = ee.batch.Task.list()
    except urllib3.exceptions.ProtocolError:
        current_app.logger.warning('Error login no GEE na hora de checkar as task')
        return jsonify([])
    gee_task = {i.id:i.state for i in all_task if i.id in list(tasks_in_queue)}

    for id_ in tasks_in_queue:
        i = tasks_in_queue[id_]
        try:
            state = gee_task[id_]
            
            if state == 'FAILED':
                state = error_in_task(ee.batch.Task(id_,'','').status())
        except:
            __task = ee.batch.Task(id_,'','').status()
            state = __task['state']
            if state == 'FAILED':
                state = error_in_task(__task)
            current_app.logger.warning(f'state obitdo de forma bruta {id_} {state}')
        i.update(state=type_process(state))
        queue.append(i.to_json())
        
    return jsonify(queue)