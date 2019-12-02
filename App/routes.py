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

APP_NAME = "KoKoS-Bullinger"
database = BullingerDB(db.session)


@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    """ welcome """
    return render_template("index.html", title=APP_NAME)


@app.route('/admin', methods=['post', 'get'])
def admin():
    return render_template('admin.html', title="Admin")


@app.route('/admin/setup', methods=['POST', 'GET'])
def setup():
    # PASSWORD PROTECTION NEEDED
    BullingerDB.setup(db.session, "Karteikarten/OCR")
    return redirect(url_for('admin'))


@app.route('/login', methods=['post', 'get'])
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
@app.route('/overview', methods=['post', 'get'])
@login_required
def overview():
    year_count = CountDict()  # year --> letter count
    for d in Datum.query:
        year_count.add(d.jahr_a)
    unclear_count = CountDict()
    closed_count = CountDict()
    invalid_count = CountDict()
    open_count = CountDict()
    r = (db.session.query(Datum, Kartei).filter(Datum.id_brief == Kartei.id_brief).all())
    for i in r:
        if i[1].status == 'abgeschlossen':
            closed_count.add(i[0].jahr_a)
        if i[1].status == 'unklar':
            unclear_count.add(i[0].jahr_a)
        if i[1].status == 'ungültig':
            invalid_count.add(i[0].jahr_a)
        if i[1].status == 'offen':
            open_count.add(i[0].jahr_a)

    data = {}
    for key in year_count:
        data[key] = [year_count[key], open_count[key], unclear_count[key], closed_count[key], invalid_count[key]]

    return render_template('overview.html', title="Übersicht", data=data)


# - months
@app.route('/overview_year/<year>', methods=['POST', 'GET'])
@login_required
def overview_year(year):
    month_count = CountDict()
    unclear_count = CountDict()
    closed_count = CountDict()
    invalid_count = CountDict()
    open_count = CountDict()
    for d in Datum.query.filter_by(jahr_a=year):
        month_count.add(d.monat_a)
    r = (db.session.query(Datum, Kartei).filter((Datum.id_brief == Kartei.id_brief) & (Datum.jahr_a == year)).all())
    for i in r:
        if i[1].status == 'abgeschlossen':
            closed_count.add(i[0].monat_a)
        if i[1].status == 'unklar':
            unclear_count.add(i[0].monat_a)
        if i[1].status == 'ungültig':
            invalid_count.add(i[0].monat_a)
        if i[1].status == 'offen':
            open_count.add(i[0].monat_a)
    data = {}
    for key in month_count:
        data[key] = [month_count[key], open_count[key], unclear_count[key], closed_count[key], invalid_count[key]]
        print(data[key])
    return render_template("overview_year.html", title="Übersicht", year=year, data=data)


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
    return render_template("overview_month.html", title="Übersicht", year=year, month=month, data=x)


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

    # handle back/forward (next/previous card)
    if card_form.prev_card.data:
        return redirect(url_for('assignment', id_brief=i - 1 if i > 1 else 10093))
    if card_form.next_card.data:
        return redirect(url_for('assignment', id_brief=i + 1 if i < 10092 else 1))

    # restore client properties
    card_form.image_height.default = session.get('image_height')
    card_form.img_height.default = session.get('img_height')
    card_form.img_width.default = session.get('img_width')

    client_variables["month"] = database.set_defaults(i, card_form)[1]

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
        database.update_user(user, number_of_changes)
        database.update_file_status(i, card_form.state.data)

    kartei = Kartei.query.filter_by(id_brief=i).first()
    client_variables["reviews"], client_variables["state"] = kartei.rezensionen, kartei.status
    client_variables["path_ocr"], client_variables["path_pdf"] = kartei.pfad_OCR, kartei.pfad_PDF
    card_form.state.default = kartei.status

    card_path = 'cards/HBBW_Karteikarte_' + (5 - len(str(i))) * '0' + str(i) + '.png'
    card_form.process()

    return render_template('assignment.html',
                           card_index=i,
                           title="Nr. "+str(i),
                           card_path=card_path,
                           form=card_form,
                           variable=client_variables)
