#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# models.py
# Bernard Schroffenegger
# 20th of October, 2019

from App import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

""" DATABASE SCHEMA DEFINITIONS

    Variable/Class names (!) correspond to actual DB-Column/Relation names.
    The character '_' will be replaced by ' ' (1st subsequent letter uppercase) """


class Kartei(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    rezensionen = db.Column(db.Integer)
    status = db.Column(db.String(50))
    pfad_OCR = db.Column(db.String(100))
    pfad_PDF = db.Column(db.String(100))

    def __init__(self, id_brief=None, rezensionen=0, status="offen", pfad_ocr=None, pfad_pdf=None):
        self.id_brief = id_brief
        self.rezensionen = rezensionen
        self.status = status
        self.pfad_OCR = pfad_ocr
        self.pfad_PDF = pfad_pdf

    def __repr__(self):
        return "<Kartei {}>".format(self.id_brief)


class Datum(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    jahr_a = db.Column(db.Integer, index=True)  # frühstens
    monat_a = db.Column(db.String(9))
    tag_a = db.Column(db.Integer)
    jahr_b = db.Column(db.Integer, index=True)  # spätestens
    monat_b = db.Column(db.String(9))
    tag_b = db.Column(db.Integer)
    bemerkung = db.Column(db.String(50))
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, id_brief=None, year_a=None, month_a=None, day_a=None, year_b=None, month_b=None, day_b=None,
                 remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.jahr_a, self.monat_a, self.tag_a = year_a, month_a, day_a
        self.jahr_b, self.monat_b, self.tag_b = year_b, month_b, day_b
        self.bemerkung, self.anwender, self.zeit = remark, user, time

    def __repr__(self):
        return '<Datum {}>'.format(self.id_brief)


class Absender(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    id_person = db.Column(db.Integer)
    bemerkung = db.Column(db.String(50))
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, id_brief=None, id_person=None, remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.id_person = id_person
        self.bemerkung = remark
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Absender {}>'.format(self.id_person)


class Empfaenger(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    id_person = db.Column(db.Integer)
    bemerkung = db.Column(db.String(50))
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, id_brief=None, id_person=None, remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.id_person = id_person
        self.bemerkung = remark
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Empfänger {}>'.format(self.id_person)


class Person(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    vorname = db.Column(db.String(50))
    titel = db.Column(db.String(50))
    ort = db.Column(db.String(50))
    empfangen = db.Column(db.Integer)
    gesendet = db.Column(db.Integer)
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, name=None, forename=None, title=None, place=None, remark=None,
                 empfangen=0, gesendet=0, user=None, time=datetime.now()):
        self.name = name
        self.vorname = forename
        self.titel = title
        self.ort = place
        self.bemerkung = remark
        self.empfangen = empfangen
        self.gesendet = gesendet
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Person {}>'.format(self.name)


class Autograph(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    standort = db.Column(db.String(50))
    signatur = db.Column(db.String(50))
    umfang = db.Column(db.String(50))
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, id_brief=None, standort=None, signatur=None, umfang=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.standort = standort
        self.signatur = signatur
        self.umfang = umfang
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Autograph {}>'.format(self.standort)


class Kopie(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    standort = db.Column(db.String(50))
    signatur = db.Column(db.String(50))
    umfang = db.Column(db.String(50))
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, id_brief=None, standort=None, signatur=None, umfang=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.standort = standort
        self.signatur = signatur
        self.umfang = umfang
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Kopie {}>'.format(self.id_brief)


class Literatur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    literatur = db.Column(db.String(50))
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, id_brief=None, literature=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.literatur = literature
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Literatur {}>'.format(self.id)


class Sprache(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    sprache = db.Column(db.String(200))
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, id_brief=None, language=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.sprache = language
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Sprache {}>'.format(self.id)


class Gedruckt(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    gedruckt = db.Column(db.String(200))
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, id_brief=None, printed=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.gedruckt = printed
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Gedruckt {}>'.format(self.id)


class Bemerkung(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    bemerkung = db.Column(db.String(400))
    anwender = db.Column(db.String(50))
    zeit = db.Column(db.String(50))

    def __init__(self, id_brief=None, remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.bemerkung = remark
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Bemerkung {}>'.format(self.id)


class User(UserMixin, db.Model):

    """ E.g.:
            u = User(username='susan', email='susan@example.com')
            u.set_password('mypassword') """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    e_mail = db.Column(db.String(120), index=True, unique=True)
    changes = db.Column(db.Integer)
    finished = db.Column(db.Integer)
    password_hash = db.Column(db.String(128))
    time = db.Column(datetime)

    def __init__(self, username=None, e_mail=None, changes=0, finished=0, time=datetime.now()):
        self.username = username
        self.e_mail = e_mail
        self.changes = changes
        self.finished = finished
        self.time = time

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


@login.user_loader
def load_user(id_user):
    return User.query.get(int(id_user))
