from datetime import datetime

from bson import ObjectId
from flask import Response
from flask import request
from flask_jwt import JWTError

import models
import utils
from config import JSON_MIME


def jwt_payload_callback(user: models.User):
    from server import app
    iat = datetime.utcnow()
    exp = iat + app.config.get('JWT_EXPIRATION_DELTA')
    nbf = iat + app.config.get('JWT_NOT_BEFORE_DELTA')
    identity = str(user.id)
    return {'exp': exp, 'iat': iat, 'nbf': nbf, 'identity': identity}


def authenticate(username:str = None, password: str = ''):
    if username is not None:
        try:
            user = models.User.objects.get({'': username})
            if user.check_password(password):
                return user
            return None
        except models.User.DoesNotExist:
            return None
    return None


def identity(payload):
    user_id = payload['identity']
    try:
        return models.User.objects.get({'_id':ObjectId(user_id)})
    except models.User.DoesNotExist:
        return None

from server import app


@app.route('/test-hello')
def hello_world():
    return 'Hello World!'


@app.route('/login/', methods=['POST'], strict_slashes=False)
@utils.already_authenticated()
def login():
    data = request.get_json(force=True)
    username = data.get('username', None)
    password = data.get('password', None)

    if not username or not password:
        raise JWTError('Bad Request', 'Invalid credentials')

    identity = authenticate(username, password)

    jwt = utils.get_jwt()
    if identity:
        access_token = jwt.jwt_encode_callback(identity)
        return jwt.auth_response_callback(access_token, identity)
    else:
        raise JWTError('Bad Request', 'Invalid credentials')


@app.route('/registry/', methods=['POST'], strict_slashes=False)
@utils.already_authenticated()
def registry():
    return Response("Success")
