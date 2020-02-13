#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# __init__.py
# Bernard Schroffenegger
# 20th of October, 2019


from flask import Flask, url_for
from flask_basicauth import BasicAuth

from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, logout_user
from App.user import *
from flask_admin import Admin


# Application
app = Flask(__name__)
app.config.from_object(Config)

# Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Accounts
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = Anonymous
login_manager.login_view = 'login'
# login_manager.session_protection = "strong"
# REMEMBER_COOKIE_DURATION = datetime.timedelta(minutes=60)

from flask_admin.contrib import sqla
from werkzeug.exceptions import HTTPException
from werkzeug import Response
from flask import redirect
from flask_login import current_user

# hack to protect the admin view
# https://computableverse.com/blog/flask-admin-using-basicauth
# ---
basic_auth = BasicAuth(app)

class ModelView(sqla.ModelView):

    def is_accessible(self):
        if current_user.username != 'Admin':
            raise AuthException('Not authenticated.')
        else: return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(basic_auth.challenge())


class AuthException(HTTPException):
    def __init__(self, message):
        super(AuthException, self).__init__(message, Response(
            "You could not be authenticated. Please refresh the page.", 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'}
        ))
# ---


# no cyclic imports (!)
from App import routes, models
from App.models import Kartei, User, Datum, Person, Absender, Empfaenger, Autograph, Kopie, Sprache, Literatur,\
    Gedruckt, Bemerkung, Notiz, Tracker

# Admin
app.config['FLASK_ADMIN_SWATCH'] = 'cosmo'  # cerulean, slate, cosmo
admin = Admin(app)

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Kartei, db.session))
admin.add_view(ModelView(Person, db.session))
admin.add_view(ModelView(Datum, db.session))
admin.add_view(ModelView(Absender, db.session))
admin.add_view(ModelView(Empfaenger, db.session))
admin.add_view(ModelView(Autograph, db.session))
admin.add_view(ModelView(Kopie, db.session))
admin.add_view(ModelView(Sprache, db.session))
admin.add_view(ModelView(Literatur, db.session))
admin.add_view(ModelView(Gedruckt, db.session))
admin.add_view(ModelView(Bemerkung, db.session))
admin.add_view(ModelView(Notiz, db.session))
admin.add_view(ModelView(Tracker, db.session))
