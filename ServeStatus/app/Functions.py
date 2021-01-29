def type_process(type_):
    if type_ in ['READY','RUNNING']:
        return 'RUNNING'
    if type_ == 'COMPLETED':
        return 'COMPLETED'
    return 'IN_QUEUE'
    