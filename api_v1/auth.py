from datetime import datetime

from bson import ObjectId
from flask import Response
from flask import request
from flask_jwt import JWTError, current_identity

import models
import utils
from config import JSON_MIME
from exceptions import InvalidDataException
from input_serializers import UserSchema

from server import app


@app.route('/test-hello')
def hello_world():
    return 'Hello World!'


@app.route('/login/', methods=['POST'], strict_slashes=False)
@utils.already_authenticated()
def login():
    if current_identity:
        return utils.json_abort({
            'message': 'User has already logged in'
        }, 400)
    data = request.get_json(force=True)
    username = data.get('username', None)
    password = data.get('password', None)

    if not username or not password:
        raise JWTError('Bad Request', 'Invalid credentials')

    identity = app.authenticate(username, password)

    jwt = utils.get_jwt()
    if identity:
        access_token = jwt.jwt_encode_callback(identity)
        return jwt.auth_response_callback(access_token, identity)
    else:
        raise JWTError('Bad Request', 'Invalid credentials')


@app.route('/registry/', methods=['POST'], strict_slashes=False)
@utils.already_authenticated()
def registry():
    data = request.get_json(force=True)
    schema = UserSchema(data)
    try:
        schema.save()
        return Response("Success")
    except InvalidDataException as ex:
        return utils.json_abort({
            'message': ex.message,
            'fields': ex.fields
        }, 400)
