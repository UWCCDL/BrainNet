def put_call_to_queue(fn):
    """
    Used to put user calls of updating graphics to the queue
    :requires fn to be a function of a class which has event_queue as field
    :param fn: the function call to put into queue
    :return: none
    """
    def wrapper(*args, **kwargs):
        # args[0] == self
        args[0].event_queue.put(fn(*args, **kwargs))
    return wrapper
