from flask_moment import Moment
import logging
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_login import LoginManager
from flask_mail import Mail



app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
moment = Moment(app)
mail = Mail(app)

login.login_view = 'login'
login.login_message = ''



from populate_db import populate_db
from app import routes, models

app.cli.add_command(populate_db)

if not os.path.exists('logs'):
    os.mkdir('logs')

from app.error_handler import email_handler, file_handler
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

