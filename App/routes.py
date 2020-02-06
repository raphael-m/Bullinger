#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# routes.py
# Bernard Schroffenegger
# 20th of October, 2019

""" Implementation of different URLs (view functions) """

from App import app, login_manager
from App.forms import *
from flask import render_template, flash, redirect, url_for, make_response, jsonify, request, session
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
def not_found(error): return make_response(jsonify({'error': 'Not found'}), 404)

@login_manager.user_loader
def load_user(id_user):
    return User.query.get(int(id_user))

@app.route('/admin', methods=['POST', 'GET'])
def admin(): return render_template('admin.html', title="Admin")


@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def index():
    """ start page """
    guest_book = GuestBookForm()
    if guest_book.validate_on_submit() and guest_book.save.data:
        BullingerDB.save_comment(guest_book.comment.data, current_user.username, datetime.now())
    guest_book.process()
    letters_sent, letters_received = BullingerDB.get_bullinger_number_of_letters()
    return render_template("index.html", title=APP_NAME, form=guest_book, vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "comments": BullingerDB.get_comments(current_user.username),
        "num_sent": letters_sent,
        "num_received": letters_received
    })


def get_base_client_variables():
    c_vars = dict()
    c_vars["username"], c_vars["user_stats"] = current_user.username, BullingerDB.get_user_stats(current_user.username)
    return c_vars


@app.route('/admin/setup', methods=['POST', 'GET'])
@login_required
def setup():
    # PASSWORD PROTECTION NEEDED                                                                                    !
    BullingerDB(db.session).setup("Karteikarten/OCR")  # ~1h
    return redirect(url_for('admin'))


@app.route('/admin/delete_user/<username>', methods=['POST', 'GET'])
@login_required
def delete_user(username):
    database.remove_user(username)
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
@login_required
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
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview(None)
    return render_template('overview.html', title="Übersicht", vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "table": data_overview,
        "url_plot": plot_url,
        "num_of_cards": num_of_cards,
        "stats": data_percentages
    })


# - months
@app.route('/overview_year/<year>', methods=['POST', 'GET'])
@login_required
def overview_year(year):
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview(year)
    return render_template('overview_year.html', title="Übersicht", vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "year": year,
        "table": data_overview,
        "url_plot": plot_url,
        "num_of_cards": num_of_cards,
        "stats": data_percentages
    })


# -days
@app.route('/overview_month/<year>/<month>', methods=['POST', 'GET'])
@login_required
def overview_month(year, month):
    if month == Config.SD: month = 0
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview_month(year, month)
    month = BullingerDB.convert_month_to_str(month)
    return render_template('overview_month.html', title="Monatsübersicht", vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "year": year,
        "month": month if month else Config.SD,
        "table": data_overview,
        "url_plot": plot_url,
        "num_of_cards": num_of_cards,
        "stats": data_percentages
    })


@app.route('/stats', methods=['GET'])
@app.route('/stats/<n_top>', methods=['GET'])
def stats(n_top=50):
    n_top, id_file = int(n_top), str(int(time.time()))
    stats_languages = BullingerDB.get_language_stats()
    BullingerDB.create_plot_user_stats(current_user.username, id_file)
    BullingerDB.create_plot_lang(stats_languages, id_file)
    return render_template(
        "stats.html",
        title="Statistiken",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "n_top": n_top,
            "file_id": id_file,
            "lang_stats": stats_languages,
            "top_s": BullingerDB.get_top_n_sender(n_top),
            "top_r": BullingerDB.get_top_n_receiver(n_top),
            "top_s_gbp": BullingerDB.get_top_n_sender_ignoring_place(n_top),
            "top_r_gbp": BullingerDB.get_top_n_receiver_ignoring_place(n_top)
        }
    )


@app.route('/overview/person_by_name/<name>', methods=['GET'])
def person_by_name(name):
    return render_template(
        "overview_general.html",
        title="Statistiken",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "table": []
        }
    )

@app.route('/overview/person_by_forename/<forename>', methods=['GET'])
def person_by_forename(forename):
    return render_template(
        "overview_general.html",
        title="Statistiken",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "table": []
        }
    )

@app.route('/overview/person_by_place/<place>', methods=['GET'])
def person_by_place(place):
    return render_template(
        "overview_general.html",
        title="Statistiken",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "table": []
        }
    )


@app.route('/faq', methods=['POST', 'GET'])
def faq():
    c_vars = get_base_client_variables()
    return render_template('faq.html', title="FAQ", vars=c_vars)


@app.route('/quick_start', methods=['POST', 'GET'])
@login_required
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
    sp = "; ".join([x.sprache for x in sprache if x.sprache and x.zeit == sprache.first().zeit]) if sprache else ''
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
                "year": (date.jahr_a if date.jahr_a else None) if date else None,
                "month": (date.monat_a if date.monat_a else 0) if date else 0,
                "day": (date.tag_a if date.tag_a else None) if date else None,
                "year_b": (date.jahr_b if date.jahr_b else None) if date else None,
                "month_b": (date.monat_b if date.monat_b else 0) if date else 0,
                "day_b": (date.tag_b if date.tag_b else None) if date else None,
                "remarks": (date.bemerkung if date.bemerkung else '') if date else ''
            },
            "sender": {
                "firstname": sender.vorname if sender else '',
                "lastname": sender.name if sender else '',
                "location": sender.ort if sender else '',
                "remarks": s.bemerkung if s else '',
                "verified": s.verifiziert if s else False
            },
            "receiver": {
                "firstname": receiver.vorname if receiver else '',
                "lastname": receiver.name if receiver else '',
                "location": receiver.ort if receiver else '',
                "remarks": r.bemerkung if r else '',
                "verified": r.verifiziert if r else False
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


def _normalize_input(data):
    for key in ["language", "literature", "printed", "first_sentence", "remarks"]:  # 1st level
        data["card"][key] = BullingerDB.normalize_str_input(data["card"][key])
    for key in ["autograph", "copy"]:  # 2nd level
        for k in data["card"][key]:
            data["card"][key][k] = BullingerDB.normalize_str_input(data["card"][key][k])
    for key in ["sender", "receiver"]:  # special case: verified
        for k in data["card"][key]:
            if k == "verified": data["card"][key][k] = True if data["card"][key][k] else None
            else: data["card"][key][k] = BullingerDB.normalize_str_input(data["card"][key][k])
    for key in data["card"]["date"]:  # numbers
        if key == 'remarks':
            data["card"]["date"][key] = BullingerDB.normalize_str_input(data["card"]["date"][key])
        elif key == 'month' or key == 'month_b':
            data["card"]["date"][key] = BullingerDB.convert_month_to_int(data["card"]["date"][key])
        else: data["card"]["date"][key] = BullingerDB.normalize_int_input(data["card"]["date"][key])
    return data


@app.route('/api/assignments/<id_brief>', methods=['POST'])
# @login_required
def save_data(id_brief):
    data, user, number_of_changes, t = _normalize_input(request.get_json()), current_user.username, 0, datetime.now()
    number_of_changes += database.save_date(id_brief, data["card"]["date"], user, t)
    print("Datum", number_of_changes)
    number_of_changes += database.save_autograph(id_brief, data["card"]["autograph"], user, t)
    print("Auto", number_of_changes)
    number_of_changes += database.save_the_sender(id_brief, data["card"]["sender"], user, t)
    print("Sender", number_of_changes)
    number_of_changes += database.save_the_receiver(id_brief, data["card"]["receiver"], user, t)
    print("Empfänger", number_of_changes)
    number_of_changes += database.save_copy(id_brief, data["card"]["copy"], user, t)
    print("Kopie", number_of_changes)
    number_of_changes += database.save_literature(id_brief, data["card"]["literature"], user, t)
    print("Literatur", number_of_changes)
    number_of_changes += database.save_language(id_brief, data["card"]["language"], user, t)
    print("Sprache", number_of_changes)
    number_of_changes += database.save_printed(id_brief, data["card"]["printed"], user, t)
    print("Gedruckt", number_of_changes)
    number_of_changes += database.save_remark(id_brief, data["card"]["first_sentence"], user, t)
    print("Satz", number_of_changes)
    database.save_comment_card(id_brief, data["card"]["remarks"], user, t)
    Kartei.update_file_status(database.dbs, id_brief, data["state"])
    User.update_user(database.dbs, user, number_of_changes, data["state"])
    return redirect(url_for('assignment', id_brief=id_brief))


@app.route('/api/persons', methods=['GET'])
# @login_required
def get_persons():
    recent_sender = BullingerDB.get_most_recent_only(db.session, Absender).subquery()
    recent_receiver = BullingerDB.get_most_recent_only(db.session, Empfaenger).subquery()
    p1 = db.session.query(Person.id, recent_sender.c.id_person, Person.name, Person.vorname, Person.ort)\
        .filter(recent_sender.c.verifiziert == 1).join(recent_sender, recent_sender.c.id_person == Person.id)
    p2 = db.session.query(Person.id, recent_receiver.c.id_person, Person.name, Person.vorname, Person.ort)\
        .filter(recent_receiver.c.verifiziert == 1).join(recent_receiver, recent_receiver.c.id_person == Person.id)
    data, d = [], defaultdict(lambda: False)
    for p in p1:
        if not d[p.id_person]: data.append({"lastname": p.name, "firstname": p.vorname, "location": p.ort})
        d[p.id_person] = True
    for p in p2:
        if not d[p.id_person]: data.append({"lastname": p.name, "firstname": p.vorname, "location": p.ort})
        d[p.id_person] = True
    return jsonify(data)
