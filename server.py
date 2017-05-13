from datetime import timedelta, datetime

from flask import Flask
from flask_jwt import JWT

app = Flask(__name__)

app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_AUTH_URL_RULE'] = None
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=30)
app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']


def jwt_payload_callback(user):
    iat = datetime.utcnow()
    exp = iat + app.config.get('JWT_EXPIRATION_DELTA')
    nbf = iat + app.config.get('JWT_NOT_BEFORE_DELTA')
    identity = str(user.id)
    return {'exp': exp, 'iat': iat, 'nbf': nbf, 'identity': identity}


def authenticate(username:str = None, password: str = ''):
    if username is not None:
        try:
            user = models.User.objects.get({'username': username})
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


jwt = JWT(app, authenticate, identity)
jwt.jwt_payload_callback = jwt_payload_callback


from api_v1.auth import *
from api_v1.views import *


if __name__ == '__main__':
    app.run()
