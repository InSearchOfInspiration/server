from datetime import timedelta, datetime

from flask import Flask
from flask_jwt import JWT
from flask_cors import CORS

app = Flask(__name__)
# app.debug = True

app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_AUTH_URL_RULE'] = None
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=30)
app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']

# CORS(app, max_age=3628800, origins='*', supports_credentials=True)
CORS(app=app)
from api_v1.auth import *
from api_v1.views import *

jwt = JWT(app, authenticate, identity)
jwt.jwt_payload_callback = jwt_payload_callback

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
