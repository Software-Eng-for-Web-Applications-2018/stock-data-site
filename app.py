import config
from flask import (Flask, redirect)
from flask_sqlalchemy import SQLAlchemy
from flask_admin import (Admin, BaseView, expose)
import flask_login


class DummyHome(BaseView):
    '''Used as a placeholder to allow for app initialization.'''

    @expose('/')
    def index(self):
        return redirect('/home')


# Set application name and assets
name = 'Stock Trend Predictor'
server = Flask(name, static_folder='assets')


# Set application configuration
server.config['SECRET_KEY'] = config.SECRET_KEY
server.config['SQLALCHEMY_DATABASE_URI'] = config.SQL_DB_URI
server.config['SQLALCHEMY_ECHO'] = False
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Initalize FlaskAdmin and database connection
admin = Admin(
    name=name,
    static_url_path='/assets',
    index_view=DummyHome(name='', url='/'),
    base_template='base.html',
    template_mode='bootstrap3'
)
db = SQLAlchemy(server)
admin.init_app(server)


# Initialize login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(server)


# Bind app context to db engine
with server.app_context():
    db.Model.metadata.bind = db.engine
    import hooks
