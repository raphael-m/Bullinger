#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# routes.py
# Bernard Schroffenegger
# 20th of October, 2019

""" Implementation of different URLs (view functions) """

import os
import pandas as pd

from sqlalchemy import desc

from App import app, db
from flask import render_template, flash, redirect, url_for, request, session
from App.forms import *
from flask_login import current_user, login_user, login_required
from flask_login import logout_user
from App.models import User, Datum, Absender, Empfaenger, Autograph, Kopie, Photokopie, Abschrift, Sprache, Literatur,\
    Gedruckt, Bemerkung, Person, Kartei
from datetime import datetime
from Tools.BullingerData import BullingerData
from Tools.Dictionaries import CountDict


from Tools.OCR2 import *

SRC_PATH_DATA = "Karteikarten/"


@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    return render_template("index.html", title="Bullingerkartei")


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
        user = User(username=form.username.data, e_mail=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        u = User.query.filter_by(username=form.username.data).first()
        login_user(u, remember=True)
        return redirect(url_for('index'))
    return render_template('account_register.html', title='Registrieren', form=form)


@app.route('/admin', methods=['post', 'get'])
def admin():
    return render_template('admin.html', title="Admin")


@app.route('/assignment/<id_brief>', methods=['POST', 'GET'])
@login_required
def assignment(id_brief):

    card_form, client_variables, i = FormFileCard(), dict(), int(id_brief)

    # current image settings (keep old settings)
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

    # go back/forward (next/previous card)
    if card_form.prev_card.data:
        return redirect(url_for('assignment', id_brief=i - 1 if i > 1 else 10093))
    if card_form.next_card.data:
        return redirect(url_for('assignment', id_brief=i + 1 if i < 10092 else 1))

    # db --> form
    datum = Datum.query.filter_by(id_brief=i).order_by(desc(Datum.zeit)).first()  # date
    month = datum.monat_a
    card_form.set_date_as_default(datum)
    receiver = Empfaenger.query.filter_by(id_brief=i).order_by(desc(Empfaenger.zeit)).first()  # receiver
    if receiver:
        person = Person.query.get(receiver.id_person)
        card_form.set_receiver_as_default(person, receiver.bemerkung)
    sender = Absender.query.filter_by(id_brief=i).order_by(desc(Absender.zeit)).first()  # sender
    if sender:
        person = Person.query.get(sender.id_person)
        card_form.set_sender_as_default(person, sender.bemerkung)
    autograph = Autograph.query.filter_by(id_brief=i).order_by(desc(Autograph.zeit)).first()  # autograph
    card_form.set_autograph_as_default(autograph)
    copy = Kopie.query.filter_by(id_brief=i).order_by(desc(Kopie.zeit)).first()  # copy
    card_form.set_copy_as_default(copy)
    photo_copy = Photokopie.query.filter_by(id_brief=i).order_by(desc(Photokopie.zeit)).first()  # photocopy
    card_form.set_photocopy_as_default(photo_copy)
    transcript = Abschrift.query.filter_by(id_brief=i).order_by(desc(Abschrift.zeit)).first()  # transcript
    card_form.set_transcript_as_default(transcript)
    literatur = Literatur.query.filter_by(id_brief=i).order_by(desc(Literatur.zeit)).first()  # literature
    card_form.set_literature_as_default(literatur)
    sprache = Sprache.query.filter_by(id_brief=i).order_by(desc(Sprache.zeit))  # language
    sprache = [s for s in sprache if s.zeit == sprache.first().zeit]
    card_form.set_language_as_default(sprache)
    gedruckt = Gedruckt.query.filter_by(id_brief=i).order_by(desc(Gedruckt.zeit)).first()  # printed
    card_form.set_printed_as_default(gedruckt)
    bemerkung = Bemerkung.query.filter_by(id_brief=i).order_by(desc(Bemerkung.zeit)).first()  # remark
    card_form.set_sentence_as_default(bemerkung)

    card_path = get_card_path(i)

    # status
    kartei = Kartei.query.filter_by(id_brief=i).first()
    card_form.image_height.default = session.get('image_height')
    card_form.img_height.default = session.get('img_height')
    card_form.img_width.default = session.get('img_width')
    client_variables["reviews"], client_variables["state"] = kartei.rezensionen, kartei.status
    client_variables["path_ocr"], client_variables["path_pdf"] = kartei.pfad_OCR, kartei.pfad_PDF
    card_form.state.default = kartei.status

    # save
    time_stamp = datetime.now()
    user = current_user.username
    number_of_changes = 0
    if card_form.validate_on_submit():
        print("Form Validated")
        # Datum
        datum_old = Datum.query.filter_by(id_brief=i).order_by(desc(Datum.zeit)).first()
        if datum_old:
            new_date, n_changes = card_form.update_date(datum_old)
            number_of_changes += n_changes
            if new_date:
                new_date.id_brief = i
                new_date.anwender = user
                new_date.zeit = time_stamp
                db.session.add(new_date)
        else:  # date doesn't exist yet (this should never be the case)
            db.session.add(Datum(id_brief=i,
                year_a=card_form.year_a.data, month_a=request.form['card_month_a'], day_a=card_form.day_a.data,
                year_b=card_form.year_b.data, month_b=request.form['card_month_b'], day_b=card_form.day_b.data,
                remark=card_form.remark.data, user=user, time=time_stamp))
            number_of_changes += 7
        db.session.commit()

        autograph_old = Autograph.query.filter_by(id_brief=i).order_by(desc(Autograph.zeit)).first()
        if autograph_old:
            new_autograph, n_changes = card_form.update_autograph(autograph_old)
            number_of_changes += n_changes
            if new_autograph:
                new_autograph.id_brief = i
                new_autograph.anwender = user
                new_autograph.zeit = time_stamp
                db.session.add(new_autograph)
                db.session.commit()
        else:
            db.session.add(Autograph(id_brief=i, standort=card_form.place_autograph.data,
                                     signatur=card_form.signature_autograph.data, umfang=card_form.scope_autograph.data,
                                     user=user, time=time_stamp))
            number_of_changes += 3
            db.session.commit()

        # Empfänger
        pre = number_of_changes
        emp_old = Empfaenger.query.filter_by(id_brief=i).order_by(desc(Empfaenger.zeit)).first()
        pers_old = Person.query.filter_by(id=emp_old.id_person).order_by(desc(Person.zeit)).first()
        p_new_query = Person.query.filter_by(titel=card_form.title_receiver.data, name=card_form.name_receiver.data,
                                             vorname=card_form.forename_receiver.data, ort=card_form.place_receiver.data)\
                                             .order_by(desc(Person.zeit)).first()
        new_person = Person(title=card_form.title_receiver.data, name=card_form.name_receiver.data,
                            forename=card_form.forename_receiver.data, place=card_form.place_receiver.data,
                            user=user, time=time_stamp)
        if emp_old:
            if pers_old:
                n = card_form.differs_from_receiver(pers_old)
                if n:
                    number_of_changes += n
                    if p_new_query:  # p_new well known ==> (r_new -> p)
                        db.session.add(Empfaenger(id_brief=i, id_person=p_new_query.id, remark=card_form.remark_receiver.data,
                                                  user=user, time=time_stamp))
                    else:  # new p, new e->p
                        db.session.add(new_person)
                        db.session.commit()  # id
                        db.session.add(Empfaenger(id_brief=i, id_person=new_person.id,
                                                  remark=card_form.remark_receiver.data, user=user, time=time_stamp))
                else:  # comment changes only
                    if card_form.has_changed__receiver_comment(emp_old):
                        db.session.add(Empfaenger(id_brief=i, id_person=pers_old.id,
                                                  remark=card_form.remark_receiver.data, user=user, time=time_stamp))
                        number_of_changes += 1
            else:
                db.session.add(new_person)
                db.session.commit()  # id
                db.session.add(Empfaenger(id_brief=i, id_person=new_person.id,
                                          remark=card_form.remark_receiver.data, user=user, time=time_stamp))
                number_of_changes += 4
        else:
            if p_new_query:
                db.session.add(Empfaenger(id_brief=i, id_person=p_new_query.id, remark=card_form.remark_receiver.data,
                                          user=user, time=time_stamp))
            else:
                db.session.add(new_person)
                db.session.commit()  # id
                db.session.add(Empfaenger(id_brief=i, id_person=new_person.id,
                                          remark=card_form.remark_receiver.data, user=user, time=time_stamp))
            number_of_changes += 4
        db.session.commit()
        if number_of_changes > pre:
            card_form.set_receiver_as_default(new_person, card_form.remark_receiver.data)

        # Absender
        pre = number_of_changes
        abs_old = Absender.query.filter_by(id_brief=i).order_by(desc(Absender.zeit)).first()
        pers_old = Person.query.filter_by(id=abs_old.id_person).order_by(desc(Person.zeit)).first()
        p_new_query = Person.query.filter_by(titel=card_form.title_sender.data, name=card_form.name_sender.data,
                                             vorname=card_form.forename_sender.data, ort=card_form.place_sender.data)\
                                             .order_by(desc(Person.zeit)).first()
        new_person = Person(title=card_form.title_sender.data, name=card_form.name_sender.data,
                            forename=card_form.forename_sender.data, place=card_form.place_sender.data,
                            user=user, time=time_stamp)
        if abs_old:
            if pers_old:
                n = card_form.differences_from_sender(pers_old)
                if n:
                    number_of_changes += n
                    if p_new_query:  # p_new well known ==> (r_new -> p)
                        db.session.add(Absender(id_brief=i, id_person=p_new_query.id,
                                                remark=card_form.remark_sender.data, user=user, time=time_stamp))
                    else:  # new p, new e->p
                        db.session.add(new_person)
                        db.session.commit()  # id
                        db.session.add(Absender(id_brief=i, id_person=new_person.id,
                                                remark=card_form.remark_sender.data, user=user, time=time_stamp))
                else:  # comment changes only
                    if card_form.has_changed__sender_comment(abs_old):
                        db.session.add(Absender(id_brief=i, id_person=pers_old.id,
                                                  remark=card_form.remark_sender.data, user=user, time=time_stamp))
                        number_of_changes += 1
            else:
                db.session.add(new_person)
                db.session.commit()  # id
                db.session.add(Absender(id_brief=i, id_person=new_person.id,
                                          remark=card_form.remark_sender.data, user=user, time=time_stamp))
                number_of_changes += 4
        else:
            if p_new_query:
                db.session.add(Absender(id_brief=i, id_person=p_new_query.id, remark=card_form.remark_sender.data,
                                          user=user, time=time_stamp))
            else:
                db.session.add(new_person)
                db.session.commit()  # id
                db.session.add(Absender(id_brief=i, id_person=new_person.id,
                                          remark=card_form.remark_sender.data, user=user, time=time_stamp))
        db.session.commit()
        if number_of_changes > pre:
            card_form.set_sender_as_default(new_person, card_form.remark_sender.data)

        # Kopie
        copy_old = Kopie.query.filter_by(id_brief=i).order_by(desc(Kopie.zeit)).first()
        if copy_old:
            new_copy, n_changes = card_form.update_copy(copy_old)
            number_of_changes += n_changes
            if new_copy:
                new_copy.id_brief = i
                new_copy.anwender = user
                new_copy.zeit = time_stamp
                db.session.add(new_copy)
                db.session.commit()
        else:
            db.session.add(Kopie(id_brief=i, standort=card_form.place_copy.data,
                                 signatur=card_form.signature_copy.data, umfang=card_form.scope_copy.data,
                                 user=user, time=time_stamp))
            number_of_changes += 3
            db.session.commit()

        # Photokopie
        pc_old = Photokopie.query.filter_by(id_brief=i).order_by(desc(Photokopie.zeit)).first()
        if pc_old:
            new_pc, n_changes = card_form.update_photocopy(pc_old)
            number_of_changes += n_changes
            if new_pc:
                new_pc.id_brief = i
                new_pc.anwender = user
                new_pc.zeit = time_stamp
                db.session.add(new_pc)
                db.session.commit()
        else:
            db.session.add(Photokopie(id_brief=i, standort=card_form.place_copy.data,
                                      bull_corr=card_form.bull_corr_photocopy.data,
                                      blatt=card_form.paper_photocopy.data,
                                      seite=card_form.page_photocopy.data,
                                      user=user, time=time_stamp))
            number_of_changes += 4
            db.session.commit()

        # Abschrift
        Literatur_old = Abschrift.query.filter_by(id_brief=i).order_by(desc(Abschrift.zeit)).first()
        if Literatur_old:
            new_literatur, n_changes = card_form.update_transcript(Literatur_old)
            number_of_changes += n_changes
            if new_literatur:
                new_literatur.id_brief = i
                new_literatur.anwender = user
                new_literatur.zeit = time_stamp
                db.session.add(new_literatur)
                db.session.commit()
        else:
            db.session.add(Abschrift(id_brief=i, standort=card_form.place_transcript.data,
                                     bull_corr=card_form.bull_corr_transcript.data,
                                     blatt=card_form.paper_transcript.data,
                                     seite=card_form.page_transcript.data,
                                     user=user, time=time_stamp))
            number_of_changes += 4
        db.session.commit()

        # Literatur
        literatur_old = Literatur.query.filter_by(id_brief=i).order_by(desc(Literatur.zeit)).first()
        if literatur_old:
            new_literatur, n_changes = card_form.update_literature(literatur_old)
            number_of_changes += n_changes
            if new_literatur:
                new_literatur.id_brief = i
                new_literatur.anwender = user
                new_literatur.zeit = time_stamp
                db.session.add(new_literatur)
                db.session.commit()
        else:
            db.session.add(Literatur(id_brief=i, literature=card_form.literature.data, user=user, time=time_stamp))
            number_of_changes += 1
            db.session.commit()

        # Sprache (there might be multiple entries)
        sprache_old = Sprache.query.filter_by(id_brief=i).order_by(desc(Sprache.zeit)).first()  # most recent
        sprache_old = Sprache.query.filter_by(id_brief=i).filter_by(zeit=sprache_old.zeit).order_by(desc(Sprache.zeit))
        if sprache_old:
            new_sprachen, n_changes = card_form.update_language(sprache_old)
            number_of_changes += n_changes
            if not new_sprachen:
                db.session.add(Sprache(id_brief=i, language='', user=user, time=time_stamp))
            else:
                for s in new_sprachen:
                    s.id_brief = i
                    s.anwender = user
                    s.zeit = time_stamp
                    db.session.add(s)
            db.session.commit()
        else:
            for s in card_form.split_lang(card_form.language.data):
                db.session.add(Sprache(id_brief=i, language=s, user=user, time=time_stamp))
                number_of_changes += 1
            db.session.commit()

        # new default
        sprache = Sprache.query.filter_by(id_brief=i).order_by(desc(Sprache.zeit))
        sprache = [s for s in sprache if s.zeit == sprache.first().zeit]
        card_form.set_language_as_default(sprache)

        # Gedruckt
        gedruckt_old = Gedruckt.query.filter_by(id_brief=i).order_by(desc(Gedruckt.zeit)).first()
        if gedruckt_old:
            new_gedruckt, n_changes = card_form.update_printed(gedruckt_old)
            if new_gedruckt:
                new_gedruckt.id_brief = i
                new_gedruckt.anwender = user
                new_gedruckt.zeit = time_stamp
                db.session.add(new_gedruckt)
                db.session.commit()
        else:
            db.session.add(Gedruckt(id_brief=i, printed=card_form.printed.data, user=user, time=time_stamp))
            number_of_changes += 1
            db.session.commit()

        # Bemerkung
        sentence_old = Bemerkung.query.filter_by(id_brief=i).order_by(desc(Bemerkung.zeit)).first()
        if sentence_old:
            new_bemerkung, n_changes = card_form.update_sentence(sentence_old)
            number_of_changes += n_changes
            if new_bemerkung:
                new_bemerkung.id_brief = i
                new_bemerkung.anwender = user
                new_bemerkung.zeit = time_stamp
                db.session.add(new_bemerkung)
                db.session.commit()
        else:
            db.session.add(Bemerkung(id_brief=i, remark=card_form.sentence.data, user=user, time=time_stamp))
            number_of_changes += 1
            db.session.commit()

        # user changes
        user = User.query.filter_by(username=user).first()
        if not user.changes:
            user.changes = 0
        user.changes += number_of_changes
        db.session.commit()

        # state update
        card_index = Kartei.query.filter_by(id_brief=i).first()
        card_index.status = card_form.state.data
        card_index.rezensionen += 1
        db.session.commit()

        # update client variables
        client_variables["reviews"], client_variables["state"] = kartei.rezensionen, kartei.status
        card_form.state.default = kartei.status



    card_form.process()
    return render_template('assignment.html', title="Nr. "+str(i), form=card_form, variable=client_variables,
                           month=month, card_index=i, card_path=card_path)


def get_card_path(card_index):
    return 'cards/HBBW_Karteikarte_'+(5-len(str(card_index)))*'0'+str(card_index)+'.png'


def create_date_selection(selection):
    date = { "s.d.": True,
        "Januar": False,
        "Februar": False,
        "März": False,
        "April": False,
        "Mai": False,
        "Juni": False,
        "Juli": False,
        "August": False,
        "September": False,
        "Oktober": False,
        "November": False,
        "Dezember": False
    }
    if selection and selection != "s.d.":
        date["s.d."] = False
        if selection in date: date[selection] = True
        else: date["s.d."] = True
    return date


@app.route('/card', methods=['post', 'get'])
def card():
    form = FormFileCard()
    user, t = str(current_user.username), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    id_ = 42  # BRIEF NUMMER  <--------
    if form.validate_on_submit():
        db.session.add(Datum(
            id_brief=id_, year_a=form.year_a.data, month_a=request.form['card_month_a'], day_a=form.day_a.data,
            year_b=form.year_b.data, month_b=request.form['card_month_b'], day_b=form.day_b.data,
            remark=form.remark.data, user=user, time=t))

        db.session.add(Person(title=form.title_sender.data, name=form.name_sender.data,
                              forename=form.forename_sender.data, place=form.place_sender.data, user=user, time=t))
        db.session.add(Person(title=form.title_receiver.data, name=form.name_receiver.data,
                              forename=form.forename_receiver.data, place=form.place_receiver.data, user=user, time=t))
        db.session.add(Absender(id_brief=id_, id_person=0, remark=form.remark_sender.data, user=user, time=t))
        db.session.add(Empfaenger(id_brief=id_, id_person=0, remark=form.remark_receiver.data, user=user, time=t))

        db.session.add(Autograph(
            id_brief=id_, standort=form.place_autograph.data, signatur=form.signature_autograph.data,
            umfang=form.scope_autograph.data, user=user, time=t))
        db.session.add(Kopie(
            id_brief=id_, standort=form.place_copy.data, signatur=form.signature_copy.data, umfang=form.scope_copy.data,
            user=user, time=t))
        db.session.add(Photokopie(
            id_brief=id_, standort=form.place_photocopy.data, bull_corr=form.bull_corr_photocopy.data,
            blatt=form.paper_photocopy.data, seite=form.page_photocopy.data, user=user, time=t))
        db.session.add(Abschrift(
            id_brief=id_, standort=form.place_transcript.data, bull_corr=form.bull_corr_transcript.data,
            blatt=form.paper_transcript.data, seite=form.page_transcript.data, user=user, time=t))
        db.session.add(Sprache(id_brief=id_, language=form.language.data, user=user, time=t))
        db.session.add(Literatur(id_brief=id_, literature=form.literature.data, user=user, time=t))
        db.session.add(Gedruckt(id_brief=id_, printed=form.printed.data, user=user, time=t))
        db.session.add(Bemerkung(id_brief=id_, remark=form.remark.data, user=user, time=t))
        db.session.commit()
        return redirect(url_for('index'))

    print(form.errors)

    return render_template('card.html', title="Karteikarten", form=form)


# Years
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


# Months
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


# Days
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


# DB
# --
@app.route('/admin/create_index', methods=['POST', 'GET'])
def create_index():
    db.session.query(Kartei).delete()
    for i in range(1, 10094):
        zeros = (5-len(str(i)))*'0'
        pdf = os.path.join(SRC_PATH_DATA+"PDF", "HBBW_Karteikarte_"+zeros+str(i)+".pdf")
        ocr = os.path.join(SRC_PATH_DATA+"OCR", "HBBW_Karteikarte_"+zeros+str(i)+".ocr")
        c = Kartei(id_brief=i, pfad_pdf=pdf, pfad_ocr=ocr)
        db.session.add(c)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin/read', methods=['POST', 'GET'])
def read():
    # BullingerData.test_card()
    BullingerData.export("Karteikarten/OCR", db.session)
    # BullingerData.get_sub_contents("Karteikarten/OCR")
    return redirect(url_for('admin'))


@app.route('/admin/delete', methods=['post', 'get'])
def delete():
    db.session.query(User).delete()
    db.session.query(Datum).delete()
    db.session.query(Person).delete()
    db.session.query(Absender).delete()
    db.session.query(Empfaenger).delete()
    db.session.query(Autograph).delete()
    db.session.query(Kopie).delete()
    db.session.query(Photokopie).delete()
    db.session.query(Abschrift).delete()
    db.session.query(Sprache).delete()
    db.session.query(Literatur).delete()
    db.session.query(Gedruckt).delete()
    db.session.query(Bemerkung).delete()
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin/analyze', methods=['post', 'get'])
def analyze():

    for e in Empfaenger.query.all():
        p = Person.query.get(e.id_person)
        p.empfangen = p.empfangen+1 if p.empfangen else 1

    for a in Absender.query.all():
        p = Person.query.get(a.id_person)
        p.gesendet = p.gesendet+1 if p.gesendet else 1
    db.session.commit()

    return redirect(url_for('admin'))


@app.route('/admin/wrong_bullingers', methods=['post', 'get'])
def wrong_bullingers():
    """ 89 Karten
    [864, 3483, 2066, 2783, 4254, 5788, 6079, 6159, 6429, 6698, 6742, 6846, 6969, 7008, 7013, 7070, 7093, 7112, 7126,
    7144, 7244, 7285, 7296, 7403, 7460, 7479, 7505, 7603, 7632, 7634, 7684, 7706, 7734, 7744, 7800, 7841, 7848, 8268,
    8279, 8384, 8437, 8438, 8567, 8712, 8724, 8749, 8756, 8801, 8814, 8845, 8857, 8871, 8928, 9000, 9003, 9018, 9019,
    9022, 9034, 9039, 9059, 9083, 9085, 9110, 9113, 9121, 9122, 9132, 9199, 9249, 9285, 9286, 9290, 9328, 9354, 9521,
    9571, 9580, 9608, 9609, 9661, 9665, 9716, 9815, 9848, 9863, 9928, 9934, 9944] """
    results = []
    for e in Empfaenger.query.all():
        p = Person.query.get(e.id_person)
        if p.name == "Bullinger" and p.vorname == "Heinrich" and p.titel == "":
            results.append(e.id_brief)
    for a in Absender.query.all():
        p = Person.query.get(a.id_person)
        if p.name == "Bullinger" and p.vorname == "Heinrich" and p.titel == "":
            results.append(a.id_brief)
    print(results, len(results))


@app.route('/admin/print_analysis', methods=['post', 'get'])
def print_analysis():
    df = pd.read_sql(db.session.query(Person).statement, db.session.bind)
    df = df.loc[:, "name":"gesendet"]
    df = df.fillna(0)
    df.gesendet = df.gesendet.astype(int)
    df.empfangen = df.empfangen.astype(int)

    df_e = df.sort_values(by=['empfangen'], ascending=False)
    df_a = df.sort_values(by=['gesendet'], ascending=False)

    e = df_e.to_latex(index=False)
    a = df_a.to_latex(index=False)

    return redirect(url_for('admin'))
