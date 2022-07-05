from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from datetime import *
from celery import Celery


app = Flask(__name__)
app.config.from_pyfile('config.py')
app.debug = True
env_vars_path = '/home/lotus/env_vars.env'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

csrf = CSRFProtect(app)
db = SQLAlchemy(app)

tax_group = {1: {'national': 19.0, 'international': 0.0},
             2: {'national': 7.0, 'international': 0.0},
             3: {'national': 0.0, 'international': 0.0}}


@app.context_processor
def inject_today_date():
    return {'today_date': datetime.now()}


from center import *
from api import api
from routes.settings import settings

app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(settings, url_prefix='/settings')

if __name__ == '__main__':
    app.run()
