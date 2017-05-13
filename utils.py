import json
import random
from functools import wraps

from flask import Response
from werkzeug.exceptions import abort
from flask_jwt import current_identity

from config import JSON_MIME


def json_abort(data, status):
    abort(Response(json.dumps(data), mimetype=JSON_MIME, status=status))


def already_authenticated():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if current_identity:
                json_abort({
                    'message': 'User has already logged in'
                }, 400)
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def get_jwt():
    from flask import current_app
    return current_app.extensions['jwt']


def get_random_color():
    red = random.randint(0, 255)
    green = random.randint(0, 255)
    blue = random.randint(0, 255)

    return '#{0:02x}{1:02x}{2:02x}'.format(red, green, blue)
