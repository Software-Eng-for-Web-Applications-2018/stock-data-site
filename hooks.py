# written by: Kevin Pielacki
# debugged by: Kevin Pielacki


from flask import (g, current_app)
from models import User
from app import login_manager
from flask_login import current_user


# Run query on each page load to see if user is still active
# Required by Flask-Login
@login_manager.user_loader
def load_user(id):
    return User.query.get(id)


@current_app.before_request
def before_request():
    g.user = current_user
