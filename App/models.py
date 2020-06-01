#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# models.py
# Bernard Schroffenegger
# 20th of October, 2019
from sqlalchemy import desc

from App import db
from config import Config
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

""" DATABASE SCHEMA DEFINITIONS
    ===========================
    - Variable/Class names (!) correspond to actual DB-Column/Relation names.
    - The character '_' will be replaced by ' ' (1st subsequent letter uppercase)
"""

# db-textfield lengths
LENGTH_S = 50  # status, username, time
LENGTH_M = 200  # path, name,forename, place, signature, sprache
LENGTH_B = 500  # remark, literatur, gedruckt


class Kartei(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    rezensionen = db.Column(db.Integer)
    status = db.Column(db.String(LENGTH_S))
    ist_link = db.Column(db.Integer)
    link_jahr = db.Column(db.Integer)
    link_monat = db.Column(db.Integer)
    link_tag = db.Column(db.Integer)
    pfad_OCR = db.Column(db.String(LENGTH_M))
    pfad_PDF = db.Column(db.String(LENGTH_M))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(
            self, id_brief=None, reviews=0, state=Config.S_OPEN,
            path_ocr=None, path_pdf=None,
            user=None,
            time=datetime.now()
    ):
        self.id_brief = id_brief
        self.rezensionen = reviews
        self.status = state
        self.pfad_OCR = path_ocr
        self.pfad_PDF = path_pdf
        self.anwender = user
        self.zeit = time

    @staticmethod
    def update_file_status(database, id_brief, state, user, t):
        k = Kartei.query.filter_by(id_brief=id_brief).order_by(desc(Kartei.zeit)).first()
        if k: database.add(Kartei(id_brief=id_brief, reviews=k.rezensionen+1, state=state, user=user, time=t))
        else: database.add(Kartei(id_brief=id_brief, reviews=1, state=state, user=user, time=t))
        database.commit()

    def __repr__(self):
        return "<Kartei {} {} {} {} {} {}>".format(
            self.id, self.id_brief, self.rezensionen, self.status, self.pfad_OCR, self.pfad_PDF)


class Datum(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    jahr_a = db.Column(db.Integer, index=True)
    monat_a = db.Column(db.Integer)
    tag_a = db.Column(db.Integer)
    jahr_b = db.Column(db.Integer, index=True)
    monat_b = db.Column(db.Integer)
    tag_b = db.Column(db.Integer)
    bemerkung = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(
        self, id_brief=None, year_a=None, month_a=None,
        day_a=None, year_b=None, month_b=None, day_b=None,
        remark=None, user=None, time=datetime.now()
    ):
        self.id_brief = id_brief
        self.jahr_a, self.monat_a, self.tag_a = year_a, month_a, day_a
        self.jahr_b, self.monat_b, self.tag_b = year_b, month_b, day_b
        self.bemerkung, self.anwender, self.zeit = remark, user, time

    def __repr__(self):
        return '<Datum {} {} {} {} {} {} {} {} {} {} {}>'.format(
            self.id, self.id_brief,
            self.jahr_a, self.monat_a, self.tag_a,
            self.jahr_b, self.monat_b, self.tag_b,
            self.bemerkung, self.anwender, self.zeit
        )


class Absender(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    id_person = db.Column(db.Integer)
    nicht_verifiziert = db.Column(db.Boolean)
    bemerkung = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, id_person=None, not_verified=None, remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.id_person = id_person
        self.nicht_verifiziert = not_verified
        self.bemerkung = remark
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Absender {} {} {} {} {} {} {}>'.format(
            self.id, self.id_brief, self.id_person, self.nicht_verifiziert, self.bemerkung, self.anwender, self.zeit)


class Empfaenger(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    id_person = db.Column(db.Integer)
    nicht_verifiziert = db.Column(db.Boolean)
    bemerkung = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, id_person=None, not_verified=None, remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.id_person = id_person
        self.nicht_verifiziert = not_verified
        self.bemerkung = remark
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Empfänger {} {} {} {} {} {} {}>'.format(
            self.id, self.id_brief, self.id_person, self.nicht_verifiziert, self.bemerkung, self.anwender, self.zeit)


class Person(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(LENGTH_M))
    vorname = db.Column(db.String(LENGTH_M))
    ort = db.Column(db.String(LENGTH_M))
    wiki_url = db.Column(db.String(LENGTH_M))
    photo = db.Column(db.String(LENGTH_M))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(
        self, name=None, forename=None, place=None, remark=None, wiki_url=None, photo=None, user=None, time=datetime.now()
    ):
        self.name = name
        self.vorname = forename
        self.ort = place
        self.bemerkung = remark
        self.wiki_url = wiki_url
        self.photo = photo
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Person {} {} {} {} {} {}>'.format(
            self.id, self.name, self.vorname, self.ort, self.anwender, self.zeit
        )

class Ortschaften(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    ort = db.Column(db.String(LENGTH_M))
    laenge = db.Column(db.String(LENGTH_M))
    breite = db.Column(db.String(LENGTH_M))

    def __init__(
        self, ort=None, l=None, b=None
    ):
        self.ort = ort
        self.laenge = l
        self.breite = b

    def __repr__(self):
        return '<Ortschaft {} {} {} {}>'.format(self.id, self.ort, self.laenge, self.breite)


class Alias(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    p_name = db.Column(db.String(LENGTH_M))
    p_vorname = db.Column(db.String(LENGTH_M))
    a_name = db.Column(db.String(LENGTH_M))
    a_vorname = db.Column(db.String(LENGTH_M))
    is_active = db.Column(db.Integer)
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, p_name=None, p_vorname=None, a_name=None, a_vorname=None, is_active=1, user=None, time=datetime.now()):
        self.p_name = p_name
        self.p_vorname = p_vorname
        self.a_name = a_name
        self.a_vorname = a_vorname
        self.is_active = is_active
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Alias {} {}>'.format(self.p_id, self.a_id)


class Autograph(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    standort = db.Column(db.String(LENGTH_M))
    signatur = db.Column(db.String(LENGTH_M))
    bemerkung = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, location=None, signature=None, remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.standort = location
        self.signatur = signature
        self.bemerkung = remark
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Autograph {} {} {} {} {} {} {}>'.format(
            self.id, self.id_brief, self.standort, self.signatur, self.bemerkung, self.anwender, self.zeit)


class Kopie(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    standort = db.Column(db.String(LENGTH_M))
    signatur = db.Column(db.String(LENGTH_M))
    bemerkung = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, location=None, signature=None, remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.standort = location
        self.signatur = signature
        self.bemerkung = remark
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Kopie {} {} {} {} {} {} {}>'.format(
            self.id, self.id_brief, self.standort, self.signatur, self.bemerkung, self.anwender, self.zeit)


class KopieB(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    standort = db.Column(db.String(LENGTH_M))
    signatur = db.Column(db.String(LENGTH_M))
    bemerkung = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, location=None, signature=None, remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.standort = location
        self.signatur = signature
        self.bemerkung = remark
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Kopie {} {} {} {} {} {} {}>'.format(
            self.id, self.id_brief, self.standort, self.signatur, self.bemerkung, self.anwender, self.zeit)


class Literatur(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    literatur = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, literature=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.literatur = literature
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Literatur {} {} {} {} {}>'.format(self.id, self.id_brief, self.literatur, self.anwender, self.zeit)


class Sprache(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    sprache = db.Column(db.String(LENGTH_M))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, language=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.sprache = language
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Sprache {} {} {} {} {}>'.format(self.id, self.id_brief, self.sprache, self.anwender, self.zeit)


class Gedruckt(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    gedruckt = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, printed=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.gedruckt = printed
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Gedruckt {} {} {} {} {}>'.format(self.id, self.id_brief, self.gedruckt, self.anwender, self.zeit)


class Bemerkung(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    bemerkung = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, remark=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.bemerkung = remark
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Bemerkung {} {} {} {} {}>'.format(self.id, self.id_brief, self.bemerkung, self.anwender, self.zeit)


class Notiz(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    id_brief = db.Column(db.Integer, index=True)
    notiz = db.Column(db.String(LENGTH_B))
    anwender = db.Column(db.String(LENGTH_S))
    zeit = db.Column(db.String(LENGTH_S))

    def __init__(self, id_brief=None, note=None, user=None, time=datetime.now()):
        self.id_brief = id_brief
        self.notiz = note
        self.anwender = user
        self.zeit = time

    def __repr__(self):
        return '<Notiz {} {} {} {} {}>'.format(self.id, self.id_brief, self.notiz, self.anwender, self.zeit)


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    e_mail = db.Column(db.String(120), index=True, unique=True)
    changes = db.Column(db.Integer)
    finished = db.Column(db.Integer)
    password_hash = db.Column(db.String(128))
    time = db.Column(db.String(LENGTH_S))

    def __init__(self, username=None, e_mail=None, hash=None, changes=0, finished=0, time=datetime.now()):
        self.username = username
        self.e_mail = e_mail
        self.changes = changes
        self.finished = finished
        self.password_hash = hash
        self.time = time

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def update_user(database, user, number_of_changes, new_state, old_state):
        user = User.query.filter_by(username=user).first()
        if user:
            user.changes += number_of_changes
            if old_state != Config.S_FINISHED and new_state == Config.S_FINISHED:
                user.finished += 1
            database.commit()

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Tracker(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(LENGTH_S))
    url = db.Column(db.String(LENGTH_M))
    time = db.Column(db.String(LENGTH_S))

    def __init__(self, username=None, url=None, time=datetime.now()):
        self.username = username
        self.url = url
        self.time = time

    def __repr__(self):
        return '<Record {} {} {} {}>'.format(self.id, self.username, self.url, self.time)
