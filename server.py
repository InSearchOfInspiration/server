from datetime import timedelta

from flask import Flask

app = Flask(__name__)

app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_AUTH_URL_RULE'] = None
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=30)
app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']


@app.route('/test-hello')
def hello_world():
    return 'Hello World!'

from api_v1 import auth


if __name__ == '__main__':
    app.run()
