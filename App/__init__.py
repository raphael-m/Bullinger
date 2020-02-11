#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# __init__.py
# Bernard Schroffenegger
# 20th of October, 2019

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from App.user import Anonymous
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

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
