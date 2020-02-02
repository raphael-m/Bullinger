#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# routes.py
# Bernard Schroffenegger
# 20th of October, 2019

""" Implementation of different URLs (view functions) """

from App import app, login
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
def not_found(error): return make_response(jsonify({'error': 'Not found'}), 404)

@login.user_loader
def load_user(id_user): return User.query.get(int(id_user))

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
def setup():
    # PASSWORD PROTECTION NEEDED                                                                                    !
    # BullingerDB.run_ocr_octopus()  # ~1-2 weeks
    BullingerDB.setup(db.session, "Karteikarten/OCR")  # ~1h
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
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview(None)
    print("adsfasdfasdfasdfasadfasdf", data_overview)
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
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview_month(year, month)
    return render_template('overview_month.html', title="Monatsübersicht", vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "year": year,
        "month": BullingerDB.convert_month(int(month)),
        "table": data_overview,
        "url_plot": plot_url,
        "num_of_cards": num_of_cards,
        "stats": data_percentages
    })


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
                "verified": s.verifiziert if s else 0
            },
            "receiver": {
                "firstname": receiver.vorname if receiver else '',
                "lastname": receiver.name if receiver else '',
                "location": receiver.ort if receiver else '',
                "remarks": r.bemerkung if r else '',
                "verified": r.verifiziert if r else ''
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
    data, user, number_of_changes, t = cleanup_input(request.get_json()), current_user.username, 0, datetime.now()
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
    Kartei.update_file_status(database.dbs, id_brief, data["state"])
    User.update_user(database.dbs, user, number_of_changes, data["state"])
    return redirect(url_for('assignment', id_brief=id_brief))


def cleanup_input(data):
    data["card"]["date"]["year"] = None if not data["card"]["date"]["year"] or data["card"]["date"]["year"] == 's.d.' else int(data["card"]["date"]["year"])
    data["card"]["date"]["month"] = None if not data["card"]["date"]["month"] or data["card"]["date"]["month"] == 's.d.' else int(data["card"]["date"]["month"])
    data["card"]["date"]["day"] = None if not data["card"]["date"]["day"] or data["card"]["date"]["day"] == 's.d.' else int(data["card"]["date"]["day"])
    data["card"]["date"]["year_b"] = None if not data["card"]["date"]["year_b"] or data["card"]["date"]["year_b"] == 's.d.' else int(data["card"]["date"]["year_b"])
    data["card"]["date"]["month_b"] = None if not data["card"]["date"]["month_b"] or data["card"]["date"]["month_b"] == 's.d.' else int(data["card"]["date"]["month_b"])
    data["card"]["date"]["day_b"] = None if not data["card"]["date"]["day_b"] or data["card"]["date"]["day_b"] == 's.d.' else int(data["card"]["date"]["day_b"])
    data["card"]["date"]["remarks"] = '' if not data["card"]["date"]["remarks"] else data["card"]["date"]["remarks"].strip()
    data["card"]["sender"]["firstname"] = '' if not data["card"]["sender"]["firstname"] else data["card"]["sender"]["firstname"].strip()
    data["card"]["sender"]["lastname"] = '' if not data["card"]["sender"]["lastname"] else data["card"]["sender"]["lastname"].strip()
    data["card"]["sender"]["location"] = '' if not data["card"]["sender"]["location"] else data["card"]["sender"]["location"].strip()
    data["card"]["sender"]["remarks"] = '' if not data["card"]["sender"]["remarks"] else data["card"]["sender"]["remarks"].strip()
    data["card"]["sender"]["verified"] = None if not data["card"]["sender"]["verified"] else True
    data["card"]["receiver"]["firstname"] = '' if not data["card"]["receiver"]["firstname"] else data["card"]["receiver"]["firstname"].strip()
    data["card"]["receiver"]["lastname"] = '' if not data["card"]["receiver"]["lastname"] else data["card"]["receiver"]["lastname"].strip()
    data["card"]["receiver"]["location"] = '' if not data["card"]["receiver"]["location"] else data["card"]["receiver"]["location"].strip()
    data["card"]["receiver"]["remarks"] = '' if not data["card"]["receiver"]["remarks"] else data["card"]["receiver"]["remarks"].strip()
    data["card"]["receiver"]["verified"] = None if not data["card"]["receiver"]["verified"] else True
    data["card"]["autograph"]["location"] = '' if not data["card"]["autograph"]["location"] else data["card"]["autograph"]["location"].strip()
    data["card"]["autograph"]["signature"] = '' if not data["card"]["autograph"]["signature"] else data["card"]["autograph"]["signature"].strip()
    data["card"]["autograph"]["remarks"] = '' if not data["card"]["autograph"]["remarks"] else data["card"]["autograph"]["remarks"].strip()
    data["card"]["copy"]["location"] = '' if not data["card"]["copy"]["location"] else data["card"]["copy"]["location"].strip()
    data["card"]["copy"]["signature"] = '' if not data["card"]["copy"]["signature"] else data["card"]["copy"]["signature"].strip()
    data["card"]["copy"]["remarks"] = '' if not data["card"]["copy"]["remarks"] else data["card"]["copy"]["remarks"].strip()
    data["card"]["language"] = '' if not data["card"]["language"] else data["card"]["language"].strip()
    data["card"]["literature"] = '' if not data["card"]["literature"] else data["card"]["literature"].strip()
    data["card"]["printed"] = '' if not data["card"]["printed"] else data["card"]["printed"].strip()
    data["card"]["first_sentence"] = '' if not data["card"]["first_sentence"] else data["card"]["first_sentence"].strip()
    data["card"]["remarks"] = '' if not data["card"]["remarks"] else data["card"]["remarks"].strip()
    return data


@app.route('/api/persons', methods=['GET'])
@login_required
def get_persons():
    recent_sender = BullingerDB.get_most_recent_only(db.session, Absender).subquery()
    recent_receiver = BullingerDB.get_most_recent_only(db.session, Empfaenger).subquery()
    p1 = db.session.query(Person.id, recent_sender.c.id_person, Person.name, Person.vorname, Person.ort)\
        .filter(recent_sender.c.verifiziert == 1).join(recent_sender, recent_sender.c.id_person == Person.id)
    p2 = db.session.query(Person.id, recent_receiver.c.id_person, Person.name, Person.vorname, Person.ort)\
        .filter(recent_receiver.c.verifiziert == 1).join(recent_receiver, recent_receiver.c.id_person == Person.id)
    d = defaultdict(lambda: False)
    for p in p1: d[p.id_person] = True
    a_ids = [{"lastname": p.name, "firstname": p.vorname, "location": p.ort} for p in p1]
    e_ids = [{"lastname": p.name, "firstname": p.vorname, "location": p.ort} for p in p2 if not d[p.id_person]]
    print(a_ids+e_ids)
    return jsonify(a_ids+e_ids)
