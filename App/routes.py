#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# routes.py
# Bernard Schroffenegger
# 20th of October, 2019

""" Implementation of different URLs (view functions) """

from App import app, login_manager
from App.forms import *
from flask import render_template, flash, redirect, url_for, make_response, jsonify, request
from flask_login import current_user, login_user, login_required, logout_user
from Tools.BullingerDB import BullingerDB
from collections import defaultdict
from App.models import *
from config import Config

import requests
import re
import time

APP_NAME = "KoKoS-Bullinger"
ADMINS = []

@app.errorhandler(404)
def not_found(error):
    BullingerDB.track(current_user.username, '/not_found', datetime.now())
    print(error)
    return make_response(jsonify({'error': 'Not found'}), 404)

def is_admin():
    if current_user.username == 'Admin': return True
    else: return False

@login_manager.user_loader
def load_user(id_user):
    return User.query.get(int(id_user))

"""
@app.route('/admin', methods=['POST', 'GET'])
@login_required
def admin():
    if is_admin(): return render_template('admin.html', title="Admin")
    return redirect(url_for('index', next=request.url))
"""

@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def index():
    """ start page """
    BullingerDB.track(current_user.username, '/home', datetime.now())
    guest_book = GuestBookForm()
    if guest_book.validate_on_submit() and guest_book.save.data:
        BullingerDB.save_comment(guest_book.comment.data, current_user.username, datetime.now())
    guest_book.process()
    letters_sent, letters_received = BullingerDB.get_bullinger_number_of_letters()
    n, t0, date = BullingerDB.get_number_of_page_visits()
    return render_template("index.html", title=APP_NAME, form=guest_book, vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "comments": BullingerDB.get_comments(current_user.username),
        "num_sent": letters_sent,
        "num_received": letters_received,
        "num_page_visits": n,
        "since": t0,
        "date": date,
    })

@app.route('/admin/setup', methods=['POST', 'GET'])
@login_required
def setup():
    if is_admin():
        BullingerDB(db.session).setup("Karteikarten/OCR")  # ~1h
        return redirect(url_for('admin'))
    return redirect(url_for('index', next=request.url))

@app.route('/admin/delete_user/<username>', methods=['POST', 'GET'])
@login_required
def delete_user(username):
    if is_admin():
        BullingerDB(db.session).remove_user(username)
        return redirect(url_for('admin'))
    return redirect(url_for('index', next=request.url))

@app.route('/login', methods=['POST', 'GET'])
def login():
    BullingerDB.track(current_user.username, '/login', datetime.now())
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
    BullingerDB.track(current_user.username, '/logout', datetime.now())
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    BullingerDB.track(current_user.username, '/register', datetime.now())
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
    BullingerDB.track(current_user.username, '/overview', datetime.now())
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview(None)
    persons = BullingerDB.get_persons_by_var(None, None)
    return render_template(
        'overview.html',
        title="Übersicht",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "table": data_overview,
            "persons": persons,
            "hits": len(persons),
            "table_language": BullingerDB.get_language_stats(),
            # "url_plot": plot_url,
            # "num_of_cards": num_of_cards,
            # "stats": data_percentages,
            # "status_description": ' '.join([str(num_of_cards), 'Karteikarten:'])
        }
    )

# - months
@app.route('/overview_year/<year>', methods=['POST', 'GET'])
@login_required
def overview_year(year):
    BullingerDB.track(current_user.username, '/overview/'+year, datetime.now())
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview(year)
    return render_template('overview_year.html', title="Übersicht", vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "year": year,
        "table": data_overview,
        "url_plot": plot_url,
        "num_of_cards": num_of_cards,
        "stats": data_percentages,
        "status_description": ' '.join([str(num_of_cards), 'Karteikarten vom Jahr', str(year)+':'])
    })

# -days
@app.route('/overview_month/<year>/<month>', methods=['POST', 'GET'])
@login_required
def overview_month(year, month):
    BullingerDB.track(current_user.username, '/'.join(['', str(month), str(year)]), datetime.now())
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
        "stats": data_percentages,
        "status_description": ' '.join([
            str(num_of_cards)+' Karteikarten' if num_of_cards>1 else 'einzigen Karteikarte',
            'vom' if month != Config.SD else 'mit der Angabe',
            month if month else Config.SD, year+':'
        ])
    })

@app.route('/overview/<name>/<forename>/<place>', methods=['GET'])
def overview_cards_of_person(name, forename, place):
    BullingerDB.track(current_user.username, '/overview/'+name, datetime.now())
    data = BullingerDB.get_overview_person(
        None if name == Config.SN else name,
        None if forename == Config.SN else forename,
        None if place == Config.SL else place)
    return render_template(
        "overview_general_cards.html",
        title=name + ', ' + forename + ', ' + place,
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "name": name,
            "forename": forename,
            "place": place,
            "table": data,
            "hits": len(data),
        }
    )

@app.route('/overview/<lang>', methods=['GET'])
def overview_languages(lang):
    BullingerDB.track(current_user.username, 'overview/'+lang, datetime.now())
    data = BullingerDB.get_overview_languages(None if lang == Config.NONE else lang)
    return render_template(
        "overview_languages_cards.html",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "language": lang,
            "table": data,
            "hits": len(data)
        }
    )

@app.route('/stats', methods=['GET'])
@app.route('/stats/<n_top>', methods=['GET'])
@login_required
def stats(n_top=50):
    BullingerDB.track(current_user.username, '/stats', datetime.now())
    n_top, id_file = int(n_top), str(int(time.time()))
    stats_languages = BullingerDB.get_language_stats()
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview(None)
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
            "top_r_gbp": BullingerDB.get_top_n_receiver_ignoring_place(n_top),
            "stats": data_percentages,
            "url_plot": plot_url,
            "status_description": ' '.join([str(num_of_cards), 'Karteikarten:'])
        }
    )

@app.route('/overview/person_by_name/<name>', methods=['GET'])
def person_by_name(name):
    BullingerDB.track(current_user.username, '/overview/'+name, datetime.now())
    data = BullingerDB.get_persons_by_var(None if name == Config.SN else name, 0)
    return render_template(
        "overview_general.html",
        title="Statistiken",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "attribute": "Nachname",
            "value": name,
            "table": data,
            "hits": str(len(data)),
            "description": "Personen mit Nachname "+name
        }
    )

@app.route('/overview/person_by_forename/<forename>', methods=['GET'])
def person_by_forename(forename):
    BullingerDB.track(current_user.username, '/overview/' + forename, datetime.now())
    data = BullingerDB.get_persons_by_var(None if forename == Config.SN else forename, 1)
    return render_template(
        "overview_general.html",
        title="Statistiken",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "attribute": "Vorname",
            "value": forename,
            "table": data,
            "hits": str(len(data)),
            "description": "Personen mit Vorname "+forename
        }
    )

@app.route('/overview/person_by_place/<place>', methods=['GET'])
def person_by_place(place):
    BullingerDB.track(current_user.username, '/overview/' + place, datetime.now())
    data = BullingerDB.get_persons_by_var(None if place == Config.SL else place, 2)
    return render_template(
        "overview_general.html",
        title="Statistiken",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "attribute": "Ort",
            "value": place,
            "table": data,
            "hits": str(len(data)),
            "description": "Personen von "+place
        }
    )

@app.route('/faq', methods=['POST', 'GET'])
def faq():
    BullingerDB.track(current_user.username, '/faq', datetime.now())
    return render_template(
        'faq.html',
        title="FAQ",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username)
        }
    )


@app.route('/quick_start', methods=['POST', 'GET'])
@login_required
def quick_start():
    BullingerDB.track(current_user.username, '/start', datetime.now())
    i = BullingerDB.quick_start()
    if i: return redirect(url_for('assignment', id_brief=str(i)))
    return redirect(url_for('overview'))  # we are done !

@app.route('/assignment/<id_brief>', methods=['GET'])
@login_required
def assignment(id_brief):
    BullingerDB.track(current_user.username, '/card/' + str(id_brief), datetime.now())
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
    kartei = Kartei.query.filter_by(id_brief=id_brief).order_by(desc(Kartei.zeit)).first()
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
@login_required
def save_data(id_brief):
    bdb = BullingerDB(db.session)
    data, user, number_of_changes, t = _normalize_input(request.get_json()), current_user.username, 0, datetime.now()
    number_of_changes += bdb.save_date(id_brief, data["card"]["date"], user, t)
    number_of_changes += bdb.save_autograph(id_brief, data["card"]["autograph"], user, t)
    number_of_changes += bdb.save_the_sender(id_brief, data["card"]["sender"], user, t)
    number_of_changes += bdb.save_the_receiver(id_brief, data["card"]["receiver"], user, t)
    number_of_changes += bdb.save_copy(id_brief, data["card"]["copy"], user, t)
    number_of_changes += bdb.save_literature(id_brief, data["card"]["literature"], user, t)
    number_of_changes += bdb.save_language(id_brief, data["card"]["language"], user, t)
    number_of_changes += bdb.save_printed(id_brief, data["card"]["printed"], user, t)
    number_of_changes += bdb.save_remark(id_brief, data["card"]["first_sentence"], user, t)
    bdb.save_comment_card(id_brief, data["card"]["remarks"], user, t)
    Kartei.update_file_status(db.session, id_brief, data["state"], user, t)
    User.update_user(db.session, user, number_of_changes, data["state"])
    return redirect(url_for('assignment', id_brief=id_brief))

@app.route('/api/persons', methods=['GET'])
@login_required
def get_persons():  # verified persons only
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
