from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy()
db.init_app(app)

from FlaskApp.views import *
from FlaskApp.api import *

if __name__ == '__main__':
    app.run(debug=True)