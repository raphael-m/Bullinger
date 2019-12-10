#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# routes.py
# Bernard Schroffenegger
# 20th of October, 2019

""" Implementation of different URLs (view functions) """

from App import app, db
from App.forms import *
from App.models import User, Kartei
from flask import render_template, flash, redirect, url_for, session
from flask_login import current_user, login_user, login_required, logout_user
from datetime import datetime
from Tools.BullingerDB import BullingerDB
from Tools.Dictionaries import CountDict
from Tools.Plots import BarChart

import time

APP_NAME = "KoKoS-Bullinger"
database = BullingerDB(db.session)


@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    """ welcome """
    return render_template("index.html", title=APP_NAME)


@app.route('/admin', methods=['POST', 'GET'])
def admin():
    return render_template('admin.html', title="Admin")


@app.route('/admin/setup', methods=['POST', 'GET'])
def setup():
    # PASSWORD PROTECTION NEEDED
    BullingerDB.setup(db.session, "Karteikarten/OCR")
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
    return render_template('account_login.html', title='Anmelden', form=form)


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
    return render_template('account_register.html', title='Registrieren', form=form)


# Overviews
# - year
@app.route('/overview', methods=['POST', 'GET'])
@login_required
def overview():
    [view_count, open_count, unclear_count, closed_count, invalid_count], id_, s = BullingerDB.get_status_counts(None)
    data = {}
    for key in view_count:
        data[key] = [view_count[key], open_count[key], unclear_count[key], closed_count[key], invalid_count[key]]
    return render_template('overview.html', title="Übersicht", data=data, img_id=id_, count=s[0], stats=s[1])


# - months
@app.route('/overview_year/<year>', methods=['POST', 'GET'])
@login_required
def overview_year(year):
    [view_count, open_count, unclear_count, closed_count, invalid_count], id_, s = BullingerDB.get_status_counts(year)
    data = {}
    for key in view_count:
        data[key] = [view_count[key], open_count[key], unclear_count[key], closed_count[key], invalid_count[key]]
    return render_template("overview_year.html", title="Übersicht", year=year, data=data, img_id=id_, count=s[0], stats=s[1])


# -days
@app.route('/overview_month/<year>/<month>', methods=['POST', 'GET'])
@login_required
def overview_month(year, month):
    x = dict()
    for d in Datum.query.filter_by(jahr_a=year, monat_a=month):
        r = Kartei.query.filter_by(id_brief=d.id_brief).first().rezensionen
        s = Kartei.query.filter_by(id_brief=d.id_brief).first().status
        dot_or_not = '.' if d.tag_a != "s.d." else ''
        date = str(d.tag_a) + dot_or_not + ' ' + d.monat_a + ' ' + str(d.jahr_a)
        x[d.id_brief] = [d.id_brief, date, r, s]
    cd = CountDict()
    for i in x: cd.add(x[i][3])
    s = BullingerDB.get_status_evaluation(cd["offen"], cd["abgeschlossen"], cd["unklar"], cd["ungültig"])
    file_name = year+'_'+month+'_'+str(int(time.time()))
    BarChart.create_plot_overview(file_name, cd["offen"], cd["abgeschlossen"], cd["unklar"], cd["ungültig"])
    return render_template("overview_month.html", title="Übersicht", year=year, month=month, data=x,
                           count=s[0], stats=s[1], file_name_stats=file_name)


@app.route('/stats', methods=['POST', 'GET'])
def stats():
    data_stats = BullingerDB.get_user_stats(current_user.username)
    file_name = str(int(time.time()))
    BullingerDB.create_plot_user_stats(current_user.username, file_name)
    sent, received = BullingerDB.get_stats_sent_received(150, 50)
    return render_template("stats.html", title="Statistiken", data=data_stats, file_name=file_name,
                           sent=sent, received=received)


@app.route('/quick_start', methods=['POST', 'GET'])
def quick_start():
    i = BullingerDB.quick_start()
    if i:  # next card with status 'offen' or 'unklar'
        return redirect(url_for('assignment', id_brief=str(i)))
    return redirect(url_for('overview'))


@app.route('/assignment/<id_brief>', methods=['POST', 'GET'])
@login_required
def assignment(id_brief):

    card_form, client_variables, i = FormFileCard(), dict(), int(id_brief)

    # client properties
    h = card_form.image_height.data
    if 'image_height' in session:  # img window
        if h: session['image_height'] = h
    else: session['image_height'] = h if h else 345
    height, width = card_form.img_height.data, card_form.img_width.data
    if 'img_height' in session:
        if height:
            session["img_height"] = height
            session["img_width"] = width
    else:
        if height:
            session["img_height"] = height
            session["img_width"] = width
        else: session["img_width"] = '100%'

    # next/previous card
    if card_form.prev_card.data:  # <
        return redirect(url_for('assignment', id_brief=BullingerDB.get_prev_card_number(i)))
    elif card_form.next_card.data:  # >
        return redirect(url_for('assignment', id_brief=BullingerDB.get_next_card_number(i)))
    elif card_form.qs_prev_card.data:  # <<
        i = BullingerDB.get_prev_assignment(i)
        if i: return redirect(url_for('assignment', id_brief=i))
        return redirect(url_for('index'))  # we are done !
    elif card_form.qs_next_card.data:  # >>
        i = BullingerDB.get_next_assignment(i)
        if i: return redirect(url_for('assignment', id_brief=i))
        return redirect(url_for('index'))  # we are done !

    # restore client properties
    card_form.image_height.default = session.get('image_height')
    card_form.img_height.default = session.get('img_height')
    card_form.img_width.default = session.get('img_width')

    # save
    user, number_of_changes, t = current_user.username, 0, datetime.now()
    if card_form.validate_on_submit():
        number_of_changes += database.save_date(i, card_form, user, t)
        number_of_changes += database.save_autograph(i, card_form, user, t)
        number_of_changes += database.save_receiver(i, card_form, user, t)
        number_of_changes += database.save_sender(i, card_form, user, t)
        number_of_changes += database.save_copy(i, card_form, user, t)
        number_of_changes += database.save_literature(i, card_form, user, t)
        number_of_changes += database.save_language(i, card_form, user, t)
        number_of_changes += database.save_printed(i, card_form, user, t)
        number_of_changes += database.save_remark(i, card_form, user, t)
        database.save_comment(i, card_form, user, t)
        database.update_user(user, number_of_changes, card_form.state.data)
        database.update_file_status(i, card_form.state.data)

    kartei = Kartei.query.filter_by(id_brief=i).first()
    client_variables["reviews"], client_variables["state"] = kartei.rezensionen, kartei.status
    client_variables["path_ocr"], client_variables["path_pdf"] = kartei.pfad_OCR, kartei.pfad_PDF
    client_variables["month"] = database.set_defaults(i, card_form)[1]
    client_variables["comments"] = BullingerDB.get_comments(i, current_user.username)

    # radio buttons
    card_form.state.default = kartei.status

    card_path = 'cards/HBBW_Karteikarte_' + (5 - len(str(i))) * '0' + str(i) + '.png'
    card_form.process()

    return render_template('assignment.html',
                           card_index=i,
                           title="Nr. "+str(i),
                           card_path=card_path,
                           form=card_form,
                           variable=client_variables)
