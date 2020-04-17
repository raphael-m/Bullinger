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
from sqlalchemy import desc, func, asc
from Tools.BullingerDB import BullingerDB
from Tools.Dictionaries import CountDict
from collections import defaultdict
from App.models import *
from config import Config
from Tools.NGrams import NGrams
from Tools.Plots import BullingerPlots

import requests
import re
import time

APP_NAME = "KoKoS-Bullinger"

@app.errorhandler(404)
def not_found(error):
    # BullingerDB.track(current_user.username, '/not_found', datetime.now())
    # print(error)
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
    # letters_sent, letters_received = BullingerDB.get_bullinger_number_of_letters()
    n, t0, date = BullingerDB.get_number_of_page_visits()
    return render_template("index.html", title=APP_NAME, vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        # "num_sent": letters_sent,
        # "num_received": letters_received,
        "num_page_visits": n,
        "since": t0,
        "date": date,
    })

"""
@app.route('/admin', methods=['POST', 'GET'])
@login_required
def admin():
    return redirect(url_for('index'))
"""
@login_required
@app.route('/admin/setup', methods=['POST', 'GET'])
def setup():
    if is_admin():
        # BullingerDB(db.session).setup("Karteikarten/HBBW@out")  # ~1h
        return redirect(url_for('index'))
    # logout_user()
    return redirect(url_for('login', next=request.url))

@app.route('/admin/delete_user/<username>', methods=['POST', 'GET'])
@login_required
def delete_user(username):
    if is_admin():
        BullingerDB(db.session).remove_user(username)
        return redirect(url_for('admin.index'))
    logout_user()
    return redirect(url_for('login', next=request.url))

@app.route('/admin/print_user', methods=['POST', 'GET'])
@login_required
def print_user():
    if is_admin():
        users = User.query.all()
        with open("Data/user_data.txt", 'w') as f:
            for u in users:
                f.write(" - ".join([u.username, u.e_mail, u.password_hash])+'\n')
        with open("Data/user_addresses.txt", 'w') as f:
            for u in users:
                if "DELETED" not in u.e_mail: f.write(u.e_mail+', ')
        return redirect(url_for('admin.index'))
    return redirect(url_for('login', next=request.url))

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
def overview():
    BullingerDB.track(current_user.username, '/overview', datetime.now())
    file_id = BullingerDB.create_new_timestamp_str()
    BullingerDB.create_correspondence_plot(file_id)
    data, sums = BullingerDB.get_data_overview_years()
    return render_template(
        'overview.html',
        title="Übersicht",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "table": data,
            "sums": sums,
            "file_id": file_id
        }
    )


# - months
@app.route('/overview_year/<year>', methods=['POST', 'GET'])
def overview_year(year):
    BullingerDB.track(current_user.username, '/overview/'+year, datetime.now())
    file_id = BullingerDB.create_new_timestamp_str()
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview(year, file_id)
    data, co, cu, ci, ca = BullingerDB.get_data_overview_month_of(year)
    data_stats = BullingerDB.get_status_evaluation(co, ca, cu, ci)
    file_id = str(int(time.time()))
    BullingerPlots.create_plot_overview_stats(file_id, [co, ca, cu, ci])
    BullingerDB.create_correspondence_plot_of_year(file_id, int(year) if year != Config.SD else None)
    return render_template('overview_year.html', title="Übersicht", vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "year": year,
        "table": data,
        "sums": [co, cu, ci, ca],
        "stats": data_stats[1],
        "file_id": file_id,
        "status_description": ' '.join([str(num_of_cards), 'Karteikarten vom Jahr', str(year)+':'])
    })

# -days
@app.route('/overview_month/<year>/<month>', methods=['POST', 'GET'])
def overview_month(year, month):
    BullingerDB.track(current_user.username, '/'.join(['', str(month), str(year)]), datetime.now())
    data, co, ca, cu, ci = BullingerDB.get_data_overview_month(year, month)
    data_stats = BullingerDB.get_status_evaluation(co, ca, cu, ci)
    file_id = str(int(time.time()))
    BullingerPlots.create_plot_overview_stats(file_id, [co, ca, cu, ci])
    BullingerDB.create_correspondence_plot_of_month(file_id, year, month)
    return render_template('overview_month.html', title="Monatsübersicht", vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "year": year,
        "month": month,
        "table": data,
        "stats": data_stats[1],
        "file_id": file_id,
        "status_description": ' '.join([
            str(len(data))+' Karteikarten' if len(data) > 1 else 'einzigen Karteikarte',
            'vom' if month != Config.SD else 'mit der Angabe',
            month if month else Config.SD, year + ':'
        ])
    })


@app.route('/persons', methods=['POST', 'GET'])
def overview_persons():
    BullingerDB.track(current_user.username, '/persons', datetime.now())
    persons = BullingerDB.get_persons_by_var(None, None, get_links=True)
    print(persons)
    return render_template(
        'overview_persons.html',
        title="Korrespondenten",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "persons": persons,
        }
    )


@app.route('/overview_state/<state>', methods=['POST', 'GET'])
def overview_state(state):
    BullingerDB.track(current_user.username, '/state/'+state, datetime.now())
    data = BullingerDB.get_overview_state(state)
    return render_template('overview_state.html', title="Statusübersicht ("+state+")", vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "table": data,
        "state": state,
    })

@app.route('/overview/<name>/<forename>/<place>', methods=['GET'])
def overview_cards_of_person(name, forename, place):
    name, forename, place = name.replace("#&&", "/"), forename.replace("#&&", "/"), place.replace("#&&", "/")
    print(name, forename, place)
    BullingerDB.track(current_user.username, '/overview/'+name, datetime.now())
    data = BullingerDB.get_overview_person(
        None if name == Config.SN else name,
        None if forename == Config.SN else forename,
        None if place == Config.SL else place, get_links=True)
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
        }
    )

@app.route('/stats', methods=['GET'])
@app.route('/stats/<n_top>', methods=['GET'])
def stats(n_top=50):
    BullingerDB.track(current_user.username, '/stats', datetime.now())
    n_top, id_file = int(n_top), str(int(time.time()))
    data_overview, data_percentages, plot_url, num_of_cards = BullingerDB.get_data_overview(None, id_file)
    w1, w2, m1, m2 = BullingerDB.create_plot_user_stats(current_user.username, id_file)
    visits_today, visits_today_staff = BullingerDB.get_page_visits_plot(id_file)
    users, user_avg, n_new_users_today, active_today = BullingerDB.get_user_plot(id_file, current_user.username)
    days_remaining, state_changes_today, state_changes_total = BullingerDB.get_progress_plot(id_file)
    days_active, changes_today, changes_total = BullingerDB.get_changes_per_day_data(id_file, current_user.username)
    return render_template(
        "stats.html",
        title="Statistiken",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "page_url": "/stats",
            "file_id": id_file,
            "stats": data_percentages,
            "workers_corr": w1,
            "workers_quit": w2,
            "corr_max": m1,
            "quit_max": m2,
            "days_active": days_active,
            "days_remaining": days_remaining,
            "changes_today": changes_today,
            "changes_total": changes_total,
            "new_users_today": n_new_users_today,
            "active_users_today": active_today,
            "state_changes_today": state_changes_today,
            "state_changes_total": state_changes_total,
            "visits_today": visits_today,
            "visits_today_staff": visits_today_staff,
            "status_description": ' '.join([str(num_of_cards), 'Karteikarten:']),
            "visits": BullingerDB.get_number_of_page_visits(visits_only=True),
            "registered_users": users,
            "users_active_on_avg": user_avg
        }
    )

@app.route('/languages', methods=['GET'])
def languages():
    BullingerDB.track(current_user.username, '/languages', datetime.now())
    id_file = str(int(time.time()))
    stats_languages = BullingerDB.get_language_stats()
    BullingerDB.create_plot_lang(stats_languages, id_file)
    return render_template(
        "overview_languages.html",
        title="Sprachen",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "file_id": id_file,
            "lang_stats": stats_languages,
        }
    )

@app.route('/places', methods=['GET'])
def places():
    BullingerDB.track(current_user.username, '/places', datetime.now())
    id_file = str(int(time.time()))
    table = BullingerDB.get_data_overview_places()
    return render_template(
        "overview_places_freq.html",
        title="Ortschaften",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "file_id": id_file,
            "places": table,
        }
    )


@app.route('/correspondents', methods=['GET'])
def correspondents():
    BullingerDB.track(current_user.username, '/correspondents', datetime.now())
    data_sender = BullingerDB.get_top_n_sender_ignoring_place()
    data_receiver = BullingerDB.get_top_n_receiver_ignoring_place()
    return render_template(
        "overview_person_no_loc.html",
        title="Korrespondenten",
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "top_s_gbp": data_sender,
            "top_r_gbp": data_receiver,
        }
    )


@app.route('/overview/person_by_name/<name>', methods=['GET'])
def person_by_name(name):
    name = name.replace("#&&", "/")
    BullingerDB.track(current_user.username, '/overview/'+name, datetime.now())
    data = BullingerDB.get_persons_by_var(None if name == Config.SN else name, 0, get_links=True)
    return render_template(
        "overview_general.html",
        title="Person "+name,
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "attribute": "Nachname",
            "value": name,
            "table": data,
            "description": "Personen mit Nachname "+name
        }
    )

@app.route('/overview/person_by_forename/<forename>', methods=['GET'])
def person_by_forename(forename):
    forename = forename.replace("#&&", "/")
    BullingerDB.track(current_user.username, '/overview/' + forename, datetime.now())
    data = BullingerDB.get_persons_by_var(None if forename == Config.SN else forename, 1, get_links=True)
    return render_template(
        "overview_general.html",
        title="Person "+forename,
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "attribute": "Vorname",
            "value": forename,
            "table": data,
            "description": "Personen mit Vorname "+forename
        }
    )

@app.route('/overview/person_by_place/<place>', methods=['GET'])
def person_by_place(place):
    place = place.replace("#&&", "/")
    BullingerDB.track(current_user.username, '/overview/' + place, datetime.now())
    data = BullingerDB.get_persons_by_var(None if place == Config.SL else place, 2, get_links=True)
    return render_template(
        "overview_general.html",
        title="Personen von "+place,
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "user_stats_all": BullingerDB.get_user_stats_all(current_user.username),
            "attribute": "Ort",
            "value": place,
            "table": data,
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
            "user_stats": BullingerDB.get_user_stats(current_user.username),
        }
    )


@app.route('/guestbook', methods=['POST', 'GET'])
def guestbook():
    BullingerDB.track(current_user.username, '/gästebuch', datetime.now())
    guest_book = GuestBookForm()
    if guest_book.validate_on_submit() and guest_book.save.data:
        BullingerDB.save_comment(guest_book.comment.data, current_user.username, datetime.now())
    guest_book.process()
    return render_template(
        'guestbook.html',
        title="Gästebuch",
        form=guest_book,
        vars={
            "username": current_user.username,
            "user_stats": BullingerDB.get_user_stats(current_user.username),
            "comments": BullingerDB.get_comments(current_user.username),
        }
    )


@app.route('/quick_start', methods=['POST', 'GET'])
@login_required
def quick_start():
    BullingerDB.track(current_user.username, '/start', datetime.now())
    i = BullingerDB.quick_start()
    if i: return redirect(url_for('assignment', id_brief=str(i)))
    return redirect(url_for('stats'))  # we are done !

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

# 1
@app.route('/api/wiki_data/<id_brief>', methods=['GET'])
def send_wiki_data_by_id(id_brief):
    link = None
    r = Empfaenger.query.filter_by(id_brief=id_brief).order_by(desc(Empfaenger.zeit)).first()
    receiver = Person.query.get(r.id_person) if r else None
    r_wiki_url, r_photo = "", ""
    if receiver:
        p = Person.query.filter_by(name=receiver.name, vorname=receiver.vorname, ort=receiver.ort).first()
        r_wiki_url, r_photo = p.wiki_url, p.photo
        if receiver.name != 'Bullinger': link = receiver.name
    s = Absender.query.filter_by(id_brief=id_brief).order_by(desc(Absender.zeit)).first()
    sender = Person.query.get(s.id_person) if s else None
    s_wiki_url, s_photo = "", ""
    if sender:
        p = Person.query.filter_by(name=sender.name, vorname=sender.vorname, ort=sender.ort).first()
        s_wiki_url, s_photo = p.wiki_url, p.photo
        if sender.name != 'Bullinger': link = sender.name
    return jsonify({
        "s_wiki_url": s_wiki_url,
        "s_photo_url": s_photo,
        "r_wiki_url": r_wiki_url,
        "r_photo_url": r_photo,
        "url_person_overview": "/overview/person_by_name/" + link if link else 's.n.'
    })

# 2
@app.route('/api/wiki_data/<name>/<forename>/<location>', methods=['GET'])
def send_wiki_data_by_address(name, forename, location):
    link = None
    wiki_url, photo_url = "", ""
    r = Person.query.filter_by(name=name, vorname=forename, ort=location).first()
    if r:
        wiki_url, photo_url = r.wiki_url, r.photo
        link = r.name
    return jsonify({
        "wiki_url": wiki_url,
        "photo_url": photo_url,
        "url_person_overview": "/overview/person_by_name/" + link if link else 's.n.'
    })


# 3
@app.route('/api/wiki_data/<name>/<forename>', methods=['GET'])
def send_wiki_data_by_address_3(name, forename):
    link = None
    wiki_url, photo_url = "", ""
    pers = Person.query.filter_by(name=name, vorname=forename).all()
    for r in pers:
        link = r.name
        if r.wiki_url or r.photo:
            wiki_url, photo_url = r.wiki_url, r.photo
            break
    return jsonify({
        "wiki_url": wiki_url,
        "photo_url": photo_url,
        "url_person_overview": "/overview/person_by_name/" + link if link else 's.n.'
    })


@app.route('/api/assignments/<id_brief>', methods=['GET'])
@login_required
def send_data(id_brief):
    id_brief = int(id_brief)
    kartei = Kartei.query.filter_by(id_brief=id_brief).order_by(desc(Kartei.zeit)).first()
    date = Datum.query.filter_by(id_brief=id_brief).order_by(desc(Datum.zeit)).first()
    r = Empfaenger.query.filter_by(id_brief=id_brief).order_by(desc(Empfaenger.zeit)).first()
    receiver = Person.query.get(r.id_person) if r else None
    r_wiki_url, r_photo = "", ""
    if receiver:
        p = Person.query.filter_by(name=receiver.name, vorname=receiver.vorname, ort=receiver.ort).first()
        r_wiki_url, r_photo = p.wiki_url, p.photo
    s = Absender.query.filter_by(id_brief=id_brief).order_by(desc(Absender.zeit)).first()
    sender = Person.query.get(s.id_person) if s else None
    s_wiki_url, s_photo = "", ""
    if sender:
        p = Person.query.filter_by(name=sender.name, vorname=sender.vorname, ort=sender.ort).first()
        s_wiki_url, s_photo = p.wiki_url, p.photo
    autograph = Autograph.query.filter_by(id_brief=id_brief).order_by(desc(Autograph.zeit)).first()
    copy = Kopie.query.filter_by(id_brief=id_brief).order_by(desc(Kopie.zeit)).first()
    literatur = Literatur.query.filter_by(id_brief=id_brief).order_by(desc(Literatur.zeit)).first()
    sprache = Sprache.query.filter_by(id_brief=id_brief).order_by(desc(Sprache.zeit))
    sp = "; ".join([x.sprache for x in sprache if x.sprache and x.zeit == sprache.first().zeit]) if sprache else ''
    gedruckt = Gedruckt.query.filter_by(id_brief=id_brief).order_by(desc(Gedruckt.zeit)).first()
    satz = Bemerkung.query.filter_by(id_brief=id_brief).order_by(desc(Bemerkung.zeit)).first()
    notiz = Notiz.query.filter_by(id_brief=id_brief).order_by(desc(Notiz.zeit)).first()
    prev_card_nr, next_card_nr = BullingerDB.get_prev_card_number(id_brief), BullingerDB.get_next_card_number(id_brief)
    prev_assignment, next_assignment = BullingerDB.get_prev_assignment(id_brief), BullingerDB.get_next_assignment(id_brief)
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
                "not_verified": s.nicht_verifiziert if s and s.nicht_verifiziert else False,
                "s_wiki_url": s_wiki_url,
                "s_photo_url": s_photo,
            },
            "receiver": {
                "firstname": receiver.vorname if receiver else '',
                "lastname": receiver.name if receiver else '',
                "location": receiver.ort if receiver else '',
                "remarks": r.bemerkung if r else '',
                "not_verified": r.nicht_verifiziert if r and r.nicht_verifiziert else False,
                "r_wiki_url": r_wiki_url,
                "r_photo_url": r_photo,
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
            "next": "/assignment/"+str(next_card_nr),
            "next_unedited": ("/assignment/"+str(next_assignment)) if next_assignment else '/stats',
            "previous": "/assignment/"+str(prev_card_nr),
            "previous_unedited": ("/assignment/"+str(prev_assignment)) if prev_assignment else '/stats'
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
            if k == "not_verified": data["card"][key][k] = True if data["card"][key][k] else None
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
    old_state = BullingerDB.get_most_recent_only(db.session, Kartei).filter_by(id_brief=id_brief).first().status
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
    User.update_user(db.session, user, number_of_changes, data["state"], old_state)
    return redirect(url_for('assignment', id_brief=id_brief))

@app.route('/api/persons', methods=['GET'])
def get_persons():  # verified persons only
    """ TODO: introduction of a separate relation for verified addresses?
    DON'T !
    recent_sender = BullingerDB.get_most_recent_only(db.session, Absender).subquery()
    recent_receiver = BullingerDB.get_most_recent_only(db.session, Empfaenger).subquery()
    p1 = db.session.query(Person.id, recent_sender.c.id_person, Person.name, Person.vorname, Person.ort)\
        .filter(recent_sender.c.anwender != Config.ADMIN)\
        .filter(recent_sender.c.nicht_verifiziert == None)\
        .join(recent_sender, recent_sender.c.id_person == Person.id)
    # cation: "== None" may not be replaced with "is None" here!
    p2 = db.session.query(Person.id, recent_receiver.c.id_person, Person.name, Person.vorname, Person.ort)\
        .filter(recent_sender.c.anwender != Config.ADMIN)\
        .filter(recent_receiver.c.nicht_verifiziert == None)\
        .join(recent_receiver, recent_receiver.c.id_person == Person.id)
    data, d = [], defaultdict(lambda: False)
    # this is shit
    for p in p1:
        if not d[p.id_person]: data.append({"lastname": p.name, "firstname": p.vorname, "location": p.ort})
        d[p.id_person] = True
    for p in p2:
        if not d[p.id_person]: data.append({"lastname": p.name, "firstname": p.vorname, "location": p.ort})
        d[p.id_person] = True
    return jsonify(data)
    """
    return jsonify([])


# 4 Steven
@app.route('/api/get_correspondence/<name>/<forename>/<location>', methods=['GET'])
def get_correspondences_all(name, forename, location):
    BullingerDB.track(current_user.username, '/api/correspondences', datetime.now())
    name = name if name and name != '0' and name != 'None' else None
    forename = forename if forename and forename != '0' and forename != 'None' else None
    location = location if location and location != '0' and location != 'None' else None
    return jsonify(BullingerDB.get_timeline_data_all(name=name, forename=forename, location=location))


@app.route('/api/get_persons', methods=['GET'])
def get_persons_all():
    BullingerDB.track(current_user.username, '/api/get_persons', datetime.now())
    return jsonify(BullingerDB.get_persons_by_var(None, None))


@app.route('/persons/alias', methods=['POST', 'GET'])
@login_required
def alias():
    BullingerDB.track(current_user.username, '/alias', datetime.now())
    p_data, form = [], PersonNameForm()
    if form.validate_on_submit():
        alias = Alias.query.filter_by(
            p_name=form.p_name.data, p_vorname=form.p_forename.data,
            a_name=form.a_name.data, a_vorname=form.a_forename.data).first()
        if alias:
            if not alias.is_active:
                alias.is_active = 1
                db.session.commit()
            return redirect(url_for('alias'))
        else:
            db.session.add(Alias(
                p_name=form.p_name.data, p_vorname=form.p_forename.data,
                a_name =form.a_name.data, a_vorname=form.a_forename.data,
                user=current_user.username, time=datetime.now()
            )); db.session.commit()

    for m in db.session.query(Alias.p_name, Alias.p_vorname).group_by(Alias.p_name, Alias.p_vorname).all():
        data = []
        for a in Alias.query.filter_by(p_name=m.p_name, p_vorname=m.p_vorname, is_active=1).all():
            data.append([a.a_name, a.a_vorname])
        if len(data): p_data.append([m.p_name, m.p_vorname, data])

    form.process()
    return render_template('person_aliases.html', title="Alias", form=form, vars={
        "username": current_user.username,
        "user_stats": BullingerDB.get_user_stats(current_user.username),
        "primary_names": p_data
    })

@app.route('/delete_alias_1/<nn>/<vn>', methods=['POST', 'GET'])
@login_required
def delete_alias_1(nn, vn):
    for a in Alias.query.filter_by(p_name=nn, p_vorname=vn, is_active=1).all(): a.is_active = 0
    db.session.commit()
    return redirect(url_for('alias'))

@app.route('/delete_alias_2/<nn>/<vn>', methods=['POST', 'GET'])
@login_required
def delete_alias_2(nn, vn):
    for a in Alias.query.filter_by(a_name=nn, a_vorname=vn, is_active=1).all(): a.is_active = 0
    db.session.commit()
    return redirect(url_for('alias'))

@app.route('/api/clear/not_found', methods=['GET'])
def clear_not_found():
    Tracker.query.filter_by(url="/not_found").delete()
    db.session.commit()
    return redirect(url_for('index'))

'''
@app.route('/api/post_process', methods=['GET'])
def post_process():
    BullingerDB.post_process_db()
    return jsonify(BullingerDB.get_persons_by_var(None, None))


@app.route('/admin/run_corrections', methods=['GET'])
@login_required
def run_corrections():
    if is_admin():
        name_corrections_general = [
            [[None, "Matthias", "Reichenweier"], ["Erb", "Matthias", "Reichenweier"]],
            [[None, "Mathias", "Reichenweier"], ["Erb", "Mathias", "Reichenweier"]],
            [[None, "Mathias", "Rappoltsweiler"], ["Erb", "Mathias", "Rappoltsweiler"]],
            [[None, "Matthias", "Rappoltsweiler"], ["Erb", "Matthias", "Rappoltsweiler"]],
            [[None, "Mathias", None], ["Erb", "Mathias", None]],
            [[None, "Richard", "London"], ["Cox", "Richard", "London"]],
            [[None, "Richard", "Westminster"], ["Cox", "Richard", "Westminster"]],
            [[None, "Richard", None], ["Cox", "Richard", None]],
            [["Chur", None, None], ["Egli", "Tobias", None]],
            [["Schlüsselberger", None, "Girenbad"], ["Schlüsselberger", "Gabriel", "Girenbad"]],
            [[None, "Stetten Georg", "Augsburg"], ["von Stetten", "Georg", "Augsburg"]],
            [["Stetten", "Georg rem", "Augsburg"], ["von Stetten", "Georg", "Augsburg"]],
            [["Stetten", "Georg vog", "Augsburg"], ["von Stetten", "Georg", "Augsburg"]],
            [["Stetten", "Georg rem", "Augsburg"], ["von Stetten", "Georg", "Augsburg"]],
            [["Stottern", "Georg vom", "Augsburg"], ["von Stetten", "Georg", "Augsburg"]],
            [["Johannes", "Georgiern", "Bern"], ["Haller", "Johannes", "Bern"]],
            [["", "Johannes", "Bern"], ["Haller", "Johannes", "Bern"]],
            [[None, "Lasco Johannes", "London"], ["Lasco", "Johannes", "Bern"]],
            [[None, "Lasco Johannes", "Emden"], ["Lasco", "Johannes", "Emden"]],
            [["Stetten", "Georg Ton", "Augsburg"], ["von Stetten", "Georg", "Augsburg"]],
            [[None, "Bellievre Jean", "Augsburg"], ["de Bellièvre", "Jean", "Solothurn"]],
            [[None, "Antorff Antwerpen", "Neue Zeitung"], ["Uss", "Antorff (Antwerpen)", "(Neue Zeitung)"]],
            [[None, "Chur", "Neue Zeitung"], ["Uss", "Chur", "Neue Zeitung"]],
            [[None, "Stetten Georg dJ", "Augsburg"], ["von Stetten", "Georg der Jüngere", "Augsburg"]],
            [[None, "Wittgenstein Ludwig", "Heidelberg"], ["Wittgenstein", "Ludwig", "Heidelberg"]],
            [[None, "llicius Philipp", "Chur"], ["Gallicius", "Philipp", "Chur"]],
            [[None, "lvin Johannes", "Genf"], ["Calvin", "Johannes", "Genf"]],
            [["BlarerAmbrosius", None, "Winterthur"], ["Blarer", "Ambrosius", "Winterthur"]],
            [["Schenk", None, "Augsburg"], ["Schenck", "Matthias", "Augsburg"]],
            [["Sozin", None, "Basel"], ["Sozin", "Laelius", "Basel"]],
            [["StGallen", "Prediger", "St. Gallen"], ["Prediger", None, "St. Gallen"]],
            [["StGaller", "Prediger", "St. Gallen"], ["Prediger", None, "St. Gallen"]],
            [["StGaller", "Geistliche", "St. Gallen"], ["Geistliche", None, "St. Gallen"]],
            [["firner", "Johann Konrad", "Schaffhausen"], ["firner", "Johann Konrad", "Ulmer"]],
            [["luSlnger", "Bs Rudolf", None], ["Bullinger", "Hans Rudolf", None]],
            [["luiliier", "Hans Rudolf", None], ["Bullinger", "Hans Rudolf", None]],
            [["lullInger", "Haus Rudelf", None], ["Bullinger", "Hans Rudolf", None]],
            [["lullInger", "Sans Budelf", None], ["Bullinger", "Hans Rudolf", None]],
            [["lullingr", "Harns Bmdelf", None], ["Bullinger", "Hans Rudolf", None]],
            [["lulllager", "ams Rudolf", None], ["Bullinger", "Hans Rudolf", None]],
        ]
        name_corrections = [
            [['Efll', 'feil'], ['Egli']],
            [['Finok'], ['Finck']],
            [['Schüler'], ['Schuler']],
            [['Fabrieus', 'Fabriim', 'Fihbri', 'Fabrieins', 'Fabrieiu', 'Fabrlelms', 'Fafcrieius', 'Fahriims'], ['Fabricius']],
            [['Beilvre', 'BeliiSvre', 'BelliSvre', 'Bellilve'], ['de Bellièvre']],
            [['BircJmann', 'Bircftmann', 'Bircjpnann', 'Bircjtmann', 'Bircjtmann', 'Bircmann', 'Birermann', 'Bjfrrcmann'], ['Birckmann']]
        ]
        forename_corrections = [
            [['Matblas', 'Mathfcls', 'Mattblas', 'Mehlas'], ['Mathias']],
            [['Tkeoder', 'Hheodor'], ['Theodor']],
            [['Tpbias'], ['Tobias']],
            [['Victcr'], ['Victor']],
            [['Jeharmes', 'Jekazmes', 'Jokajmes', 'Jokämme', 'Jokannee', 'Joknnss', 'Jokaaae', 'Jakaanea', 'Jekeaaes', 'Jeharmes', 'Jehaaaea', 'Jokanaes'], ['Johannes']],
        ]
        place_corrections = [
            [['Cttujf', 'Cjbur', 'Gbur', 'tfhur', 'CL uv', 'CU w', 'Chfir', 'Chjpft', 'Ckar', 'Qiur', 'Cbra'], ['Chur']],
            [['Saanen'], ['Samaden']],
            [['Gi ef', 'Gjf', 's l Genf'], ['Genf']],
            [['S l', 'S t Xe', 's'], [None]]
        ]
        with open("Data/name_corr.txt", 'w') as f:
            for pair in name_corrections_general:
                fp = Person.query.filter_by(name=pair[0][0], vorname=pair[0][1], ort=pair[0][2]).all()
                if fp:
                    np = Person.query.filter_by(name=pair[1][0], vorname=pair[1][1], ort=pair[1][2]).first()
                    if not np:
                        np = Person(name=pair[1][0], forename=pair[1][1], place=pair[1][2], user=Config.ADMIN, time=datetime.now())
                        db.session.add(np)
                        db.session.commit()
                        np = Person.query.filter_by(name=pair[1][0], vorname=pair[1][1], ort=pair[1][2]).first()
                        f.write('NEW: '+(pair[1][0] if pair[1][0] else 's.n.')+", "+(pair[1][1] if pair[1][1] else 's.n.')+", "+(pair[1][2] if pair[1][2] else 's.l.')+"\n")
                    for p in fp:
                        f.write((p.name if p.name else 's.n.')+', '+(p.vorname if p.vorname else 's.n.')+', '+(p.ort if p.ort else 's.l.')+'\t-->\t'+(np.name if np.name else 's.n.')+', '+(np.vorname if np.vorname else 's.n.')+', '+(np.ort if np.ort else 's.l.')+"\n")
                        for e in Empfaenger.query.filter_by(id_person=p.id).all():
                            e.id_person = np.id
                            db.session.commit()
                            f.write('changed Empfänger on #'+str(e.id_brief)+".\n")
                        for a in Absender.query.filter_by(id_person=p.id).all():
                            a.id_person = np.id
                            db.session.commit()
                            f.write('changed Absender on #' + str(a.id_brief)+".\n")

            for pair in name_corrections:
                for n in pair[0]:
                    for p in Person.query.filter_by(name=n).all():
                        np = Person.query.filter_by(name=pair[1][0], vorname=p.vorname, ort=p.ort).first()
                        if not np:
                            np = Person(name=pair[1][0], forename=p.vorname, place=p.ort, user=Config.ADMIN, time=datetime.now())
                            db.session.add(np)
                            db.session.commit()
                            np = Person.query.filter_by(name=pair[1][0], vorname=p.vorname, ort=p.ort).first()
                            f.write('NEW: '+pair[1][0]+", "+(np.vorname if np.vorname else 's.n.')+", "+(np.ort if np.ort else 's.l.')+"\n")
                        f.write((p.name if p.name else 's.n.')+', '+(p.vorname if p.vorname else 's.n.')+', '+(p.ort if p.ort else 's.l.')+'\t-->\t'+pair[1][0]+", "+(p.vorname if p.vorname else 's.n.')+", "+(p.ort if p.ort else 's.l.')+"\n")
                        for e in Empfaenger.query.filter_by(id_person=p.id).all():
                            e.id_person = np.id
                            db.session.commit()
                            f.write('changed Empfänger on #'+str(e.id_brief)+".\n")
                        for a in Absender.query.filter_by(id_person=p.id).all():
                            a.id_person = np.id
                            db.session.commit()
                            f.write('changed Absender on #' + str(a.id_brief)+".\n")

            for pair in forename_corrections:
                for n in pair[0]:
                    for p in Person.query.filter_by(vorname=n).all():
                        np = Person.query.filter_by(name=p.name, vorname=pair[1][0], ort=p.ort).first()
                        if not np:
                            np = Person(name=p.name, forename=pair[1][0], place=p.ort, user=Config.ADMIN, time=datetime.now())
                            db.session.add(np)
                            db.session.commit()
                            np = Person.query.filter_by(name=p.name, vorname=pair[1][0], ort=p.ort).first()
                            f.write('NEW: '+(p.name if p.name else 's.n.')+", "+pair[1][0]+", "+(np.ort if p.ort else 's.l.')+"\n")
                        f.write((p.name if p.name else 's.n.')+', '+(p.vorname if p.vorname else 's.n.')+', '+(p.ort if p.ort else 's.l.')+'\t-->\t'+(p.name if p.name else 's.n.')+", "+pair[1][0]+", "+(p.ort if p.ort else 's.l.')+"\n")
                        for e in Empfaenger.query.filter_by(id_person=p.id).all():
                            e.id_person = np.id
                            db.session.commit()
                            f.write('changed Empfänger on card #'+str(e.id_brief)+".\n")
                        for a in Absender.query.filter_by(id_person=p.id).all():
                            a.id_person = np.id
                            db.session.commit()
                            f.write('changed Absender on card #' + str(a.id_brief)+".\n")

            for pair in place_corrections:
                for n in pair[0]:
                    for p in Person.query.filter_by(ort=n).all():
                        np = Person.query.filter_by(name=p.name, vorname=p.vorname, ort=pair[1][0]).first()
                        if not np:
                            np = Person(name=p.name, forename=p.vorname, place=pair[1][0], user=Config.ADMIN, time=datetime.now())
                            db.session.add(np)
                            db.session.commit()
                            np = Person.query.filter_by(name=p.name, vorname=p.vorname, ort=pair[1][0]).first()
                            f.write('NEW: '+(p.name if p.name else 's.n.')+", "+(p.vorname if p.vorname else 's.n.')+", "+pair[1][0]+"\n")
                        f.write((p.name if p.name else 's.n.')+', '+(p.vorname if p.vorname else 's.n.')+', '+(p.ort if p.ort else 's.l.')+'\t-->\t'+(p.name if p.name else 's.n.')+", "+(p.vorname if p.vorname else 's.n.')+", "+(pair[1][0] if pair[1][0] else 's.l.')+"\n")
                        for e in Empfaenger.query.filter_by(id_person=p.id).all():
                            e.id_person = np.id
                            db.session.commit()
                            f.write('changed Empfänger on #'+str(e.id_brief)+".\n")
                        for a in Absender.query.filter_by(id_person=p.id).all():
                            a.id_person = np.id
                            db.session.commit()
                            f.write('changed Absender on #' + str(a.id_brief)+".\n")

        with open("Data/sign_corr.txt", 'w') as f:
            f.write("AUTOGRAPH\n\n")
            for a in Autograph.query.filter_by(standort="Zürich StA").all():
                start = a.signatur
                if a.signatur:
                    for s in ["E ii", "E il", "E li", "E ll", "Eii", "Eil", "Eli", "Ell", "EU", "E U", "EII2", "II", "EIX"]:
                        if a.signatur[:len(s)] == s:
                            a.signatur = a.signatur.replace(s, '')
                            a.signatur = 'E II '+a.signatur.strip()
                            db.session.commit()
                    if 'f' in a.signatur:
                        new = a.signatur.replace('f', '').strip() + ' f'
                        if new != a.signatur:
                            a.signatur = new
                            db.session.commit()
                    for s in [' ,,,,', ',,,, ', ',,, ', ' ,,,', ' ,,', ',, ', ' ,',  ', ']:
                        a.signatur = a.signatur.replace(s, ' ')
                    for s in [',,,,,', ',,,,', ',,,', ',,']:
                        a.signatur = a.signatur.replace(s, ' ')
                    if a.signatur != start:
                        f.write('#'+str(a.id_brief)+':\t'+start + "\t-->\t" + a.signatur + "\n")
            f.write("\n\nKOPIE\n\n")
            for a in Kopie.query.filter_by(standort="Zürich StA").all():
                start = a.signatur
                if a.signatur:
                    for s in ["E ii", "E il", "E li", "E ll", "Eii", "Eil", "Eli", "Ell", "EU", "E U", "EII2", "II", "EIX"]:
                        if a.signatur[:len(s)] == s:
                            a.signatur = a.signatur.replace(s, '')
                            a.signatur = 'E II '+a.signatur.strip()
                            db.session.commit()
                    if 'f' in a.signatur:
                        new = a.signatur.replace('f', '').strip() + ' f'
                        if new != a.signatur:
                            a.signatur = new
                            db.session.commit()
                    for s in [' ,,,,', ',,,, ', ',,, ', ' ,,,', ' ,,', ',, ', ' ,',  ', ']:
                        a.signatur = a.signatur.replace(s, ' ')
                    for s in [',,,,,', ',,,,', ',,,', ',,']:
                        a.signatur = a.signatur.replace(s, ' ')
                    if a.signatur != start:
                        f.write('#'+str(a.id_brief)+':\t'+start + "\t-->\t" + a.signatur + "\n")

        return redirect(url_for('index'))
    return redirect(url_for('login', next=request.url))


@app.route('/admin/run_corrections2', methods=['GET'])
@login_required
def run_corrections2():
    if is_admin():

        zsta = "Zürich StA"
        with open("Data/zsta_corr2.txt", 'w') as f:
            f.write("AUTOGRAPH\n\n")
            for a in Autograph.query.all():
                p = NGrams.compute_similarity(zsta, a.standort, 3)
                if p > 0.8 and a.standort != zsta:
                    f.write('#' + str(a.id_brief) + ':\t' + a.standort + "\t-->\t" + zsta + "\n")
                    a.standort = zsta
                    db.session.commit()
            f.write("\n\nKOPIE\n\n")
            for a in Kopie.query.all():
                p = NGrams.compute_similarity(zsta, a.standort, 3)
                if p > 0.8 and a.standort != zsta:
                    f.write('#' + str(a.id_brief) + ':\t' + a.standort + "\t-->\t" + zsta + "\n")
                    a.standort = zsta
                    db.session.commit()

        zzb = "Zürich ZB"
        with open("Data/zb_corr2.txt", 'w') as f:
            f.write("AUTOGRAPH\n\n")
            for a in Autograph.query.all():
                p = NGrams.compute_similarity(zzb, a.standort, 3)
                if p > 0.8 and a.standort != zzb:
                    f.write('#' + str(a.id_brief) + ':\t' + a.standort + "\t-->\t" + zzb + "\n")
                    a.standort = zzb
                    db.session.commit()
            f.write("\n\nKOPIE\n\n")
            for a in Kopie.query.all():
                p = NGrams.compute_similarity(zzb, a.standort, 3)
                if p > 0.8 and a.standort != zzb:
                    f.write('#' + str(a.id_brief) + ':\t' + a.standort + "\t-->\t" + zzb + "\n")
                    a.standort = zzb
                    db.session.commit()

        with open("Data/sign_corr2.txt", 'w') as f:
            f.write("AUTOGRAPH\n\n")
            for a in Autograph.query.filter_by(standort="Zürich StA").all():
                start = a.signatur
                if a.signatur:
                    for s in ["E ii", "E il", "E li", "E ll", "Eii", "Eil", "Eli", "Ell", "EU", "E U", "EII2", "II", "EIX"]:
                        if a.signatur[:len(s)] == s:
                            a.signatur = a.signatur.replace(s, '')
                            a.signatur = 'E II '+a.signatur.strip()
                            db.session.commit()
                    m = re.match(r".*[^\W\d]{4,}.*", a.signatur)
                    if not m:
                        if 'f' in a.signatur:
                            new = a.signatur.replace('f', '').strip() + ' f'
                            if new != a.signatur:
                                a.signatur = new
                                db.session.commit()
                    m = re.match(r".*(\s*\,\,+\s*).*", a.signatur)
                    if m:
                        a.signatur = a.signatur.replace(m.group(1), ', ')
                        db.session.commit()
                    m = re.match(r".*\d(\s*\,\s*)\d.*", a.signatur)
                    if m and m.group(0):
                        a.signatur = a.signatur.replace(m.group(1), ',')
                        db.session.commit()
                    if a.signatur != start:
                        f.write('#'+str(a.id_brief)+':\t'+start + "\t-->\t" + a.signatur + "\n")
            f.write("\n\nKOPIE\n\n")
            for a in Kopie.query.filter_by(standort="Zürich StA").all():
                start = a.signatur
                if a.signatur:
                    for s in ["E ii", "E il", "E li", "E ll", "Eii", "Eil", "Eli", "Ell", "EU", "E U", "EII2", "II", "EIX"]:
                        if a.signatur[:len(s)] == s:
                            a.signatur = a.signatur.replace(s, '')
                            a.signatur = 'E II '+a.signatur.strip()
                            db.session.commit()
                    m = re.match(r".*[^\W\d]{4,}.*", a.signatur)
                    if not m:
                        if 'f' in a.signatur:
                            new = a.signatur.replace('f', '').strip() + ' f'
                            if new != a.signatur:
                                a.signatur = new
                                db.session.commit()
                    m = re.match(r".*(\s*\,\,+\s*).*", a.signatur)
                    if m:
                        a.signatur = a.signatur.replace(m.group(1), ', ')
                        db.session.commit()
                    m = re.match(r".*\d(\s*\,\s*)\d.*", a.signatur)
                    if m:
                        a.signatur = a.signatur.replace(m.group(1), ',')
                        db.session.commit()
                    if a.signatur != start:
                        f.write('#'+str(a.id_brief)+':\t'+start + "\t-->\t" + a.signatur + "\n")

        return redirect(url_for('index'))
    return redirect(url_for('login', next=request.url))

@app.route('/admin/convert_images', methods=['GET'])
def convert_to_images():
    input_path = "Karteikarten/PDF_new"
    output_path = "Karteikarten/PNG_new/HBBW_Karteikarte_"
    # output_path = "App/static/cards/HBBW_Karteikarte_"

    i = 1
    for file in FileSystem.get_file_paths(input_path):
        for page in convert_from_path(file, 600):
            print(file)
            path = output_path+(5-len(str(i)))*'0'+str(i)+'.png'
            page.save(path, 'PNG')
            i += 1
'''

'''
@app.route('/api/print_nn_vn_pairs', methods=['GET'])
def print_persons():
    persons = BullingerDB.get_persons_by_var(None, None)
    with open("Data/persons.txt", 'a') as out:
        pairs = set()
        for p in persons:
            if (p[0], p[1]) not in pairs:
                pairs.add((p[0], p[1]))
        for p in persons:
            if (p[0], p[1]) in pairs:
                out.write("#\t" + p[0] + '\t' + p[1] + '\n')
                pairs.remove((p[0], p[1]))
    return jsonify([])


@app.route('/api/print_locations', methods=['GET'])
def print_locations():
    with open("Data/locations.txt", 'w') as out:
        locs = set()
        d = CountDict()
        for p in Person.query.all():
            if p.ort:
                d.add(p.ort)
        print(d.get_pairs_sorted(by_value=True, reverse=True))
        for loc in d.get_pairs_sorted(by_value=True, reverse=True):
            if loc[0]:
                out.write("#\t" + loc[0] + '\n')
    return jsonify([])


@app.route('/api/compute_similarities', methods=['GET'])
def print_similarities():
    precisio = 4
    with open("Data/persons_corr.txt", 'w') as corr:
        with open("Data/persons.txt", 'r') as in_file:
            for line in in_file.readlines():
                if line.strip('\n') and line[0] != '#' and '\t' in line:
                    nn, vn = line.strip('\n').split('\t')
                    for p in Person.query.all():
                        s = (NGrams.compute_similarity(nn, p.name, precisio)+NGrams.compute_similarity(vn, p.vorname, precisio))/2
                        if s > 0.74 and s != 1.0:
                            corr.write(p.name + " " + p.vorname + "\t--->\t" + nn + " " + vn + "\n")
                            p.name, p.vorname = nn, vn
                            db.session.commit()
    with open("Data/locations_corr.txt", 'w') as corr:
        with open("Data/locations.txt", 'r') as in_file:
            for line in in_file.readlines():
                if line.strip('\n') and line[0] != '#':
                    loc = line.strip()
                    for p in Person.query.all():
                        if p.ort:
                            s = NGrams.compute_similarity(loc, p.ort, precisio)
                            if s > 0.74 and s != 1.0:
                                print(p.ort + "\t--->\t" + loc, s)
                                corr.write(p.ort + "\t--->\t" + loc + "\n")
                                p.ort = loc
                                db.session.commit()
    return jsonify([])
'''
