#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# routes.py
# Bernard Schroffenegger
# 20th of October, 2019

""" Implementation of different URLs (view functions) """

from App import app
from App.forms import *
from flask import render_template, flash, redirect, url_for, make_response, jsonify, request
from flask_login import current_user, login_user, login_required, logout_user
from Tools.BullingerDB import BullingerDB
from collections import defaultdict
from sqlalchemy import desc
from App.models import *
from config import Config

import requests
import re
import time

APP_NAME = "KoKoS-Bullinger"
database = BullingerDB(db.session)


@app.errorhandler(404)
def not_found(error):
    print(error)
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def index():
    """ start page """
    comment_form = GuestBookForm()
    if comment_form.validate_on_submit() and comment_form.save.data:
        BullingerDB.save_comment(comment_form.comment.data, current_user.username, datetime.now())
    c_vars = get_base_client_variables()
    c_vars["comments"] = BullingerDB.get_comments(current_user.username)  # validation/save first
    comment_form.process()
    return render_template("index.html", title=APP_NAME, form=comment_form, vars=c_vars)


def get_base_client_variables():
    c_vars = dict()
    c_vars["username"], c_vars["user_stats"] = current_user.username, BullingerDB.get_user_stats(current_user.username)
    return c_vars


@app.route('/admin', methods=['POST', 'GET'])
def admin():
    return render_template('admin.html', title="Admin")


@app.route('/admin/setup', methods=['POST', 'GET'])
def setup():
    # PASSWORD PROTECTION NEEDED                                                                                    !
    """ delete and setup db (runtime ~1h) """
    BullingerDB.setup(db.session, "Karteikarten/OCR")
    return redirect(url_for('admin'))


@app.route('/admin/setup_plus', methods=['POST', 'GET'])
def setup_plus():
    BullingerDB.employ_octopus()
    return redirect(url_for('admin'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('ungültige Login-Daten')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('account_login.html', title='Anmelden', form=form, username=current_user.username)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, e_mail=form.email.data, time=datetime.now())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        u = User.query.filter_by(username=form.username.data).first()
        login_user(u, remember=True)
        return redirect(url_for('index'))
    return render_template('account_register.html', title='Registrieren', form=form, username=current_user.username)


# Overviews
# - year
@app.route('/overview', methods=['POST', 'GET'])
@login_required
def overview():
    c_vars = get_base_client_variables()
    c_vars["data"], c_vars["file_id"], c_vars["count"], c_vars["stats"] = BullingerDB.get_data_overview(None)
    return render_template('overview.html', title="Übersicht", vars=c_vars)


# - months
@app.route('/overview_year/<year>', methods=['POST', 'GET'])
@login_required
def overview_year(year):
    c_vars = get_base_client_variables()
    c_vars["year"] = year
    c_vars["data"], c_vars["file_id"], c_vars["count"], c_vars["stats"] = BullingerDB.get_data_overview(year)
    return render_template("overview_year.html", title="Übersicht", vars=c_vars)


# -days
@app.route('/overview_month/<year>/<month>', methods=['POST', 'GET'])
@login_required
def overview_month(year, month):
    c_vars = get_base_client_variables()
    c_vars["year"], c_vars["month"] = year, BullingerDB.convert_month(month)
    c_vars["data"], c_vars["file_id"], c_vars["count"], c_vars["stats"] = BullingerDB.get_data_overview_month(year, month)
    return render_template("overview_month.html", title="Übersicht", vars=c_vars)


@app.route('/stats', methods=['POST', 'GET'])
def stats():
    c_vars, c_vars["n_top"] = get_base_client_variables(), 42  # n top Empfänger/Absender
    c_vars["user_stats_all"] = BullingerDB.get_user_stats_all(current_user.username)
    c_vars["lang_stats"] = BullingerDB.get_language_stats()
    c_vars["file_id"] = str(int(time.time()))
    c_vars["top_s"], c_vars["top_r"] = BullingerDB.get_stats_sent_received(c_vars["n_top"], c_vars["n_top"])
    BullingerDB.create_plot_user_stats(current_user.username, c_vars["file_id"])
    BullingerDB.create_plot_lang(c_vars["lang_stats"], c_vars["file_id"])
    return render_template("stats.html", title="Statistiken", vars=c_vars)


@app.route('/faq', methods=['POST', 'GET'])
def faq():
    c_vars = get_base_client_variables()
    return render_template('faq.html', title="FAQ", vars=c_vars)


@app.route('/quick_start', methods=['POST', 'GET'])
def quick_start():
    i = BullingerDB.quick_start()
    if i:  # next card with status 'offen' or 'unklar'
        return redirect(url_for('assignment', id_brief=str(i)))
    return redirect(url_for('overview'))  # we are done !


@app.route('/assignment/<id_brief>', methods=['GET'])
@login_required
def assignment(id_brief):
    ui_path = Config.BULLINGER_UI_PATH
    ui_path = ui_path + ("" if ui_path.endswith("/") else "/")
    # Load vue html from deployment and strip unneeded tags (html, body, doctype, title, icon, fonts etc.)
    html_content = requests.get(ui_path).text
    html_content = re.sub("<!DOCTYPE html>", "", html_content)
    html_content = re.sub("</?html.*?>", "", html_content)
    html_content = re.sub("</?meta.*?>", "", html_content)
    html_content = re.sub("<link rel=\"icon\".*?>", "", html_content)
    html_content = re.sub("<title>.*?</title>", "", html_content)
    html_content = re.sub("</?head>", "", html_content)
    html_content = re.sub("</?body>", "", html_content)
    html_content = re.sub("<link href=(\")?https://fonts.googleapis.com.*?>", "", html_content)
    html_content = re.sub("(?P<ref> (src|href)=(\")?)/", r"\g<ref>" + ui_path, html_content)
    return render_template('assignment_vue.html',
        card_index=id_brief,
        html_content=html_content)


@app.route('/api/assignments/<id_brief>', methods=['GET'])
@login_required
def send_data(id_brief):
    id_brief = int(id_brief)
    kartei = Kartei.query.filter_by(id_brief=id_brief).first()
    date = Datum.query.filter_by(id_brief=id_brief).order_by(desc(Datum.zeit)).first()
    r = Empfaenger.query.filter_by(id_brief=id_brief).order_by(desc(Empfaenger.zeit)).first()
    receiver = Person.query.get(r.id_person) if r else None
    s = Absender.query.filter_by(id_brief=id_brief).order_by(desc(Absender.zeit)).first()
    sender = Person.query.get(s.id_person) if s else None
    autograph = Autograph.query.filter_by(id_brief=id_brief).order_by(desc(Autograph.zeit)).first()
    copy = Kopie.query.filter_by(id_brief=id_brief).order_by(desc(Kopie.zeit)).first()
    literatur = Literatur.query.filter_by(id_brief=id_brief).order_by(desc(Literatur.zeit)).first()
    sprache = Sprache.query.filter_by(id_brief=id_brief).order_by(desc(Sprache.zeit))
    sp = "; ".join([s.sprache for s in sprache if s.zeit == sprache.first().zeit]) if sprache else ''
    gedruckt = Gedruckt.query.filter_by(id_brief=id_brief).order_by(desc(Gedruckt.zeit)).first()
    satz = Bemerkung.query.filter_by(id_brief=id_brief).order_by(desc(Bemerkung.zeit)).first()
    notiz = Notiz.query.filter_by(id_brief=id_brief).order_by(desc(Notiz.zeit)).first()
    data = {
        "id": id_brief,
        "state": kartei.status,
        "reviews": kartei.rezensionen,
        "card_path": '/static/cards/HBBW_Karteikarte_' + (5-len(str(id_brief)))*'0'+str(id_brief) + '.png',
        "card": {
            "date": {
                "year": (date.jahr_a if date.jahr_a else 's.d.') if date else 's.d.',
                "month": (date.monat_a if date.monat_a else 0) if date else 0,
                "day": (date.tag_a if date.tag_a else 's.d.') if date else 's.d.',
                "year_b": (date.jahr_b if date.jahr_b else 's.d.') if date else '',
                "month_b": (date.monat_b if date.monat_b else 0) if date else 0,
                "day_b": (date.tag_b if date.tag_b else 's.d.') if date else '',
                "remarks": date.bemerkung if date else ''
            },
            "sender": {
                "firstname": sender.vorname if sender else '',
                "lastname": sender.name if sender else '',
                "location": sender.ort if sender else '',
                "remarks": s.bemerkung if s else '',
                "verified": sender.verifiziert if sender else 0
            },
            "receiver": {
                "firstname": receiver.vorname if receiver else '',
                "lastname": receiver.name if receiver else '',
                "location": receiver.ort if receiver else '',
                "remarks": r.bemerkung if r else '',
                "verified": receiver.verifiziert if receiver else ''
            },
            "autograph": {
                "location": autograph.standort if autograph else '',
                "signature": autograph.signatur if autograph else '',
                "remarks": autograph.bemerkung if autograph else ''
            },
            "copy": {
                "location": copy.standort if copy else '',
                "signature": copy.signatur if copy else '',
                "remarks": copy.bemerkung if copy else ''
            },
            "language": sp,
            "literature": literatur.literatur if literatur else '',
            "printed": gedruckt.gedruckt if gedruckt else '',
            "first_sentence": satz.bemerkung if satz else '',
            "remarks": notiz.notiz if notiz else ''
        },
        "navigation": {
            "next": "/assignment/"+str(BullingerDB.get_next_card_number(id_brief)),
            "next_unedited": "/assignment/"+str(BullingerDB.get_next_assignment(id_brief)),
            "previous": "/assignment/"+str(BullingerDB.get_prev_card_number(id_brief)),
            "previous_unedited": "/assignment/"+str(BullingerDB.get_prev_assignment(id_brief))
        }
    }
    return jsonify(data)


@app.route('/api/assignments/<id_brief>', methods=['POST'])
@login_required
def save_data(id_brief):
    data, user, number_of_changes, t = request.get_json(), current_user.username, 0, datetime.now()
    number_of_changes += database.save_date(id_brief, data["card"]["date"], user, t)
    number_of_changes += database.save_autograph(id_brief, data["card"]["autograph"], user, t)
    number_of_changes += database.save_the_sender(id_brief, data["card"]["sender"], user, t)
    number_of_changes += database.save_the_receiver(id_brief, data["card"]["receiver"], user, t)
    number_of_changes += database.save_copy(id_brief, data["card"]["copy"], user, t)
    number_of_changes += database.save_literature(id_brief, data["card"]["literature"], user, t)
    number_of_changes += database.save_language(id_brief, data["card"]["language"], user, t)
    number_of_changes += database.save_printed(id_brief, data["card"]["printed"], user, t)
    number_of_changes += database.save_remark(id_brief, data["card"]["first_sentence"], user, t)
    database.save_comment_card(id_brief, data["card"]["remarks"], user, t)
    database.update_file_status(id_brief, data["state"])
    database.update_user(user, number_of_changes, data["state"])
    return redirect(url_for('assignment', id_brief=id_brief))


@app.route('/api/persons', methods=['GET'])
@login_required
def get_persons():
    recent_sender = BullingerDB.get_most_recent_only(db.session, Absender).subquery()
    recent_receiver = BullingerDB.get_most_recent_only(db.session, Empfaenger).subquery()
    p1 = db.session.query(Person.id, recent_sender.c.id_person, Person.name, Person.vorname, Person.ort)\
        .filter(Person.verifiziert == 1).join(recent_sender, recent_sender.c.id_person == Person.id)
    p2 = db.session.query(Person.id, recent_receiver.c.id_person, Person.name, Person.vorname, Person.ort)\
        .filter(Person.verifiziert == 1).join(recent_receiver, recent_receiver.c.id_person == Person.id)
    d = defaultdict(lambda: False)
    for p in p1: d[p.id_person] = True
    a_ids = [{"lastname": p.name, "firstname": p.vorname, "location": p.ort} for p in p1]
    e_ids = [{"lastname": p.name, "firstname": p.vorname, "location": p.ort} for p in p2 if not d[p.id_person]]
    return jsonify(a_ids+e_ids)
