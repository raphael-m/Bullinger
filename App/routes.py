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

import time

APP_NAME = "KoKoS-Bullinger"
database = BullingerDB(db.session)


@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def index():
    """ start page """
    comment_form = FormComments()
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
    c_vars["year"], c_vars["month"] = year, month
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


@app.route('/assignment/<id_brief>', methods=['POST', 'GET'])
@login_required
def assignment(id_brief):

    card_form, i = FormFileCard(), int(id_brief)

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
    kartei = Kartei.query.filter_by(id_brief=i).first()
    user, number_of_changes, t = current_user.username, 0, datetime.now()
    if card_form.validate_on_submit():
        number_of_changes += database.save_date(i, card_form, user, t)
        number_of_changes += database.save_autograph(i, card_form, user, t)
        number_of_changes += database.save_the_sender(i, card_form, user, t)
        number_of_changes += database.save_the_receiver(i, card_form, user, t)
        number_of_changes += database.save_copy(i, card_form, user, t)
        number_of_changes += database.save_literature(i, card_form, user, t)
        number_of_changes += database.save_language(i, card_form, user, t)
        number_of_changes += database.save_printed(i, card_form, user, t)
        number_of_changes += database.save_remark(i, card_form, user, t)
        database.save_comment_card(i, card_form, user, t)
        database.update_file_status(i, card_form.state.data)
        database.update_user(user, number_of_changes, card_form.state.data)
        if card_form.submit_and_next.data:
            return redirect(url_for('quick_start'))

    # client variables
    c_vars = get_base_client_variables()
    c_vars["reviews"], c_vars["state"] = kartei.rezensionen, kartei.status
    c_vars["path_ocr"], c_vars["path_pdf"] = kartei.pfad_OCR, kartei.pfad_PDF
    c_vars["month"] = database.set_defaults(i, card_form)[1]
    c_vars["comments"] = BullingerDB.get_comments_card(i, current_user.username)
    c_vars["user_stats"] = BullingerDB.get_user_stats(current_user.username)
    c_vars["card_path"] = 'cards/HBBW_Karteikarte_' + (5-len(str(i)))*'0'+str(i) + '.png'

    # radio buttons
    card_form.state.default = kartei.status

    card_form.process()
    return render_template('assignment.html',
                           card_index=i,
                           title="Nr. "+str(i),
                           form=card_form,
                           vars=c_vars)
