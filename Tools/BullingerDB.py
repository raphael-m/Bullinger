#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# BullingerDB.py
# Bernard Schroffenegger
# 30th of November, 2019

import os, time
import psutil
from Tools.Dictionaries import CountDict
from Tools.Plots import *
from Tools.Octopus import *
from App.models import *
from sqlalchemy import asc, desc, func, and_, or_
from operator import itemgetter
from random import sample
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as pltc
all_colors = [k for k, v in pltc.cnames.items()]

ADMIN = 'Admin'  # username (setup)
L_PROGRESS = ["offen", "abgeschlossen", "unklar", "ungültig"]  # labels (plots)
C_PROGRESS = ["navy", "forestgreen", "orange", "red"]


class BullingerDB:

    def __init__(self, database_session):
        self.dbs = database_session
        self.t = datetime.now()

    @staticmethod
    def setup(db_session, dir_path):
        """ creates the entire date base basing on ocr data """
        d, card_nr, ignored, errors = BullingerDB(db_session), 1, 0, []
        d.delete_all()
        d.add_bullinger()
        d.add_guest()
        n_grams_bullinger = NGrams.get_ngram_dicts_dicts("Bullinger", 4)
        n_grams_heinrich = NGrams.get_ngram_dicts_dicts("Heinrich", 4)
        id_bullinger = BullingerDB.get_id_bullinger()
        for path in FileSystem.get_file_paths(dir_path, recursively=False):
            print(card_nr, path)
            data = BullingerData.get_data_as_dict(path)
            d.update_timestamp()
            d.set_index(card_nr)
            if data:
                d.add_date(card_nr, data)
                d.add_correspondents(card_nr, data, [n_grams_bullinger, n_grams_heinrich], id_bullinger)
                d.add_autograph(card_nr, data)
                d.add_copy(card_nr, data)
                d.add_literature(card_nr, data)
                d.add_printed(card_nr, data)
                remark = d.add_remark(card_nr, data)
                d.add_lang(card_nr, data, remark)
            else:
                print("*** WARNING, file ignored:", path)
                d.push2db(Datum(year_a=SD, month_a=SD, day_a=SD, year_b='', month_b=SD, day_b='', remark=''), card_nr, ADMIN, d.t)
                ignored += 1
                errors.append(card_nr)
            card_nr += 1
            d.dbs.commit()
        if ignored: print("*** WARNING,", ignored, "files ignored:", errors)
        # Postprocessing
        BullingerDB.count_correspondence()

    @staticmethod
    def employ_octopus():
        """
        in_out_pairs = []
        file_ids = [d.id_brief for d in Datum.query.filter_by(jahr_a=SD, monat_a=SD, tag_a=SD).all()]
        for i in file_ids:
            file_out = 'Karteikarten/OCR_Kraken/HBBW_Karteikarte_' + (5 - len(str(i))) * '0' + str(i) + '.ocr'
            if not os.path.exists(file_out):
                file_in = 'App/static/cards/HBBW_Karteikarte_' + (5 - len(str(i))) * '0' + str(i) + '.png'
                in_out_pairs.append([file_in, file_out])
        """
        in_out_pairs = []
        file_ids = [k.id_brief for k in Kartei.query.all()]
        for i in file_ids:
            file_out = 'Karteikarten/OCR_Kraken/HBBW_Karteikarte_' + (5 - len(str(i))) * '0' + str(i) + '.ocr'
            if not os.path.exists(file_out):
                file_in = 'App/static/cards/HBBW_Karteikarte_' + (5 - len(str(i))) * '0' + str(i) + '.png'
                in_out_pairs.append([file_in, file_out])

        for pair in in_out_pairs:
            print(pair[1])
            subp = Octopus.run(pair[0], pair[1])
            p = psutil.Process(subp.pid)
            try: p.wait(timeout=60 * 1.5)
            except psutil.TimeoutExpired:
                p.kill()
                continue

    def update_timestamp(self):
        self.t = datetime.now()

    def set_index(self, i):
        zeros = (5 - len(str(i))) * '0'
        pdf = os.path.join("Karteikarten/PDF", "HBBW_Karteikarte_" + zeros + str(i) + ".pdf")
        ocr = os.path.join("Karteikarten/OCR", "HBBW_Karteikarte_" + zeros + str(i) + ".ocr")
        self.dbs.add(Kartei(id_brief=i, pfad_pdf=pdf, pfad_ocr=ocr))

    def delete_all(self):
        # self.dbs.query(User).delete()
        self.dbs.query(Kartei).delete()
        self.dbs.query(Datum).delete()
        self.dbs.query(Person).delete()
        self.dbs.query(Absender).delete()
        self.dbs.query(Empfaenger).delete()
        self.dbs.query(Autograph).delete()
        self.dbs.query(Kopie).delete()
        self.dbs.query(Sprache).delete()
        self.dbs.query(Literatur).delete()
        self.dbs.query(Gedruckt).delete()
        self.dbs.query(Bemerkung).delete()
        self.dbs.query(Notiz).delete()
        self.dbs.commit()

    def update_file_status(self, id_brief, state):
        file = Kartei.query.filter_by(id_brief=id_brief).first()
        file.status = state
        file.rezensionen += 1
        self.dbs.commit()

    def update_user(self, user, number_of_changes, state):
        user = User.query.filter_by(username=user).first()
        user.changes += number_of_changes
        user.finished += 1 if state == 'abgeschlossen' else 0
        self.dbs.commit()

    def add_bullinger(self):
        bullinger = Person(name="Bullinger", forename="Heinrich", place="Zürich", user=ADMIN, time=self.t)
        self.dbs.add(bullinger)
        self.dbs.commit()

    def add_guest(self):
        self.dbs.add(User(username='Gast', changes=0, finished=0, time=self.t))

    @staticmethod
    def get_id_bullinger():
        return Person.query.filter_by(name="Bullinger", vorname="Heinrich", ort="Zürich").first().id

    def add_date(self, card_nr, data):
        date = BullingerData.extract_date(card_nr, data)
        if not date:  # Octopus
            path = 'Karteikarten/OCR_Kraken/HBBW_Karteikarte_' + (5-len(str(card_nr)))*'0'+str(card_nr) + '.ocr'
            data = BullingerData.get_data_as_dict(path)
            if data: date = BullingerData.extract_date(card_nr, data)
            if not date: date = Datum(year_a=SD, month_a=SD, day_a=SD, year_b='', month_b=SD, day_b='', remark='')
        self.push2db(date, card_nr, ADMIN, self.t)

    def add_correspondents(self, card_nr, data, n_grams, id_bullinger):
        """ one has to be bullinger """
        if BullingerData.is_bullinger_sender(data, n_grams[0], n_grams[1]):
            self.push2db(Absender(id_person=id_bullinger, remark=''), card_nr, ADMIN, self.t)
            e = BullingerData.analyze_address(data["Empfänger"])
            if not Person.query.filter_by(name=e[0], vorname=e[1], ort=e[2]).first():
                self.push2db(Person(name=e[0], forename=e[1], place=e[2], verified='Nein'), card_nr, ADMIN, self.t)
            ref = Person.query.filter_by(name=e[0], vorname=e[1], ort=e[2]).first().id
            self.push2db(Empfaenger(id_brief=card_nr, id_person=ref, remark=e[3]), card_nr, ADMIN, self.t)
        else:
            self.push2db(Empfaenger(id_brief=card_nr, id_person=id_bullinger, remark=''), card_nr, ADMIN, self.t)
            a = BullingerData.analyze_address(data["Absender"])
            if not Person.query.filter_by(name=a[0], vorname=a[1], ort=a[2]).first():
                self.push2db(Person(name=a[0], forename=a[1], place=a[2], verified='Nein'), card_nr, ADMIN, self.t)
            ref = Person.query.filter_by(name=a[0], vorname=a[1], ort=a[2]).first().id
            self.push2db(Absender(id_brief=card_nr, id_person=ref, remark=a[3]), card_nr, ADMIN, self.t)

    def add_autograph(self, card_nr, data):
        place, signature, scope = BullingerData.get_ssu(data, "A")
        if place or signature:
            self.push2db(Autograph(standort=place, signatur=signature, umfang=scope), card_nr, ADMIN, self.t)

    def add_copy(self, card_nr, data):
        place, signature, scope = BullingerData.get_ssu(data, "B")
        if place or signature:
            self.push2db(Kopie(standort=place, signatur=signature, umfang=scope), card_nr, ADMIN, self.t)

    def add_literature(self, card_nr, data):
        literature = BullingerData.get_literature(data)
        if literature:
            self.push2db(Literatur(literature=literature), card_nr, ADMIN, self.t)

    def add_printed(self, card_nr, data):
        printed = BullingerData.get_printed(data)
        if printed:
            self.push2db(Gedruckt(printed=printed), card_nr, ADMIN, self.t)

    def add_lang(self, card_nr, data, remark):
        for lang in BullingerData.get_lang(data, remark):
            self.push2db(Sprache(language=lang), card_nr, ADMIN, self.t)

    def add_remark(self, card_nr, data):
        remark = BullingerData.get_remark(data)
        if remark:
            self.push2db(Bemerkung(remark=remark), card_nr, ADMIN, self.t)
            return remark
        return ''

    @staticmethod
    def set_defaults(id_, form):
        datum = Datum.query.filter_by(id_brief=id_).order_by(desc(Datum.zeit)).first()
        form.set_date_as_default(datum)
        receiver = Empfaenger.query.filter_by(id_brief=id_).order_by(desc(Empfaenger.zeit)).first()
        if receiver:
            form.set_receiver_as_default(Person.query.get(receiver.id_person), receiver.bemerkung)
        sender = Absender.query.filter_by(id_brief=id_).order_by(desc(Absender.zeit)).first()
        if sender:
            form.set_sender_as_default(Person.query.get(sender.id_person), sender.bemerkung)
        form.set_autograph_as_default(Autograph.query.filter_by(id_brief=id_).order_by(desc(Autograph.zeit)).first())
        form.set_copy_as_default(Kopie.query.filter_by(id_brief=id_).order_by(desc(Kopie.zeit)).first())
        form.set_literature_as_default(Literatur.query.filter_by(id_brief=id_).order_by(desc(Literatur.zeit)).first())
        sprache = Sprache.query.filter_by(id_brief=id_).order_by(desc(Sprache.zeit))
        if sprache:
            form.set_language_as_default([s for s in sprache if s.zeit == sprache.first().zeit])
        form.set_printed_as_default(Gedruckt.query.filter_by(id_brief=id_).order_by(desc(Gedruckt.zeit)).first())
        form.set_sentence_as_default(Bemerkung.query.filter_by(id_brief=id_).order_by(desc(Bemerkung.zeit)).first())
        form.set_default_state(Kartei.query.filter_by(id_brief=id_).first())
        return [datum.jahr_a, datum.monat_a, datum.tag_a]

    @staticmethod
    def count_correspondence():
        for e in Empfaenger.query.all():
            p = Person.query.get(e.id_person)
            p.empfangen = p.empfangen+1 if p.empfangen else 1
        for a in Absender.query.all():
            p = Person.query.get(a.id_person)
            p.gesendet = p.gesendet+1 if p.gesendet else 1
        db.session.commit()

    def save_date(self, i, data_date, user, t):
        datum_old, n = Datum.query.filter_by(id_brief=i).order_by(desc(Datum.zeit)).first(), 0
        if datum_old:
            new_date, n = BullingerDB.update_date(data_date, datum_old)
            self.push2db(new_date, i, user, t)
        # date doesn't exist yet (should never be the case)
        elif data_date["year"] or data_date["month"] != 0 or data_date["day"] \
                or data_date["year_b"] or data_date["month_b"] != 0 or data_date["day_b"]:
                self.push2db(Datum(
                        year_a=data_date["year"], month_a=data_date["month"], day_a=data_date["day"],
                        year_b=data_date["year_b"], month_b=data_date["month_b"], day_b=data_date["day_b"],
                        remark=data_date["remarks"]),
                    i, user, t)
                n = 7
        return n

    @staticmethod
    def update_date(data_date, datum_old):
        new_datum, n = Datum(), 0  # number of changes
        if str(datum_old.jahr_a) != str(data_date["year"]): n += 1  # year/month/day (A)
        new_datum.jahr_a = 's.d.' if not str(data_date["year"]) else str(data_date["year"])
        if datum_old.monat_a != data_date["month"]: n += 1
        new_datum.monat_a = data_date["month"]
        if str(datum_old.tag_a) != str(data_date["day"]): n += 1
        new_datum.tag_a = 's.d.' if not str(data_date["day"]) else str(data_date["day"])
        if str(datum_old.jahr_b) != str(data_date["year_b"]): n += 1  # year/month/day (B)
        new_datum.jahr_b = str(data_date["day"])
        if datum_old.monat_b != data_date["month_b"] and data_date["month_b"]: n += 1
        new_datum.monat_b = data_date["month_b"]
        if str(datum_old.tag_b) != str(data_date["day_b"]): n += 1
        new_datum.tag_b = str(data_date["day_b"])
        if datum_old.bemerkung != str(data_date["remarks"]): n += 1  # remark
        new_datum.bemerkung = data_date["remarks"].strip()
        return (new_datum, n) if n > 0 else (None, 0)

    def save_autograph(self, i, d, user, t):
        autograph_old, n = Autograph.query.filter_by(id_brief=i).order_by(desc(Autograph.zeit)).first(), 0
        if autograph_old:
            new_autograph, n = BullingerDB.update_autograph(d, autograph_old)
            self.push2db(new_autograph, i, user, t)
        elif d["location"].strip() or d["signature"].strip() or d["remarks"].strip():
            self.push2db(Autograph(standort=d["location"], signatur=d["signature"], umfang=d["remarks"]), i, user, t)
            n = 3
        self.dbs.commit()
        return n

    @staticmethod
    def update_autograph(d, autograph_old):
        new_autograph, number_of_changes = Autograph(), 0
        if autograph_old.standort != d["location"].strip(): number_of_changes += 1
        new_autograph.standort = d["location"].strip()
        if autograph_old.signatur != d["signature"].strip(): number_of_changes += 1
        new_autograph.signatur = d["signature"].strip()
        if autograph_old.bemerkung != d["remarks"].strip(): number_of_changes += 1
        new_autograph.bemerkung = d["remarks"].strip()
        return (new_autograph, number_of_changes) if number_of_changes > 0 else (None, 0)

    @staticmethod
    def get_number_of_differences_from_person(data, person):
        n = 0  # differences
        if person.name != data["lastname"].strip(): n += 1
        if person.vorname != data["firstname"].strip(): n += 1
        if person.ort != data["location"].strip(): n += 1
        if person.verifiziert != data["verified"]: n += 1
        return n

    def save_the_receiver(self, i, d, user, t):
        emp_old = Empfaenger.query.filter_by(id_brief=i).order_by(desc(Empfaenger.zeit)).first()
        pers_old = Person.query.filter_by(id=emp_old.id_person).order_by(desc(Person.zeit)).first() if emp_old else None
        p_new_query = Person.query\
            .filter_by(name=d["lastname"], vorname=d["firstname"], ort=d["location"], verifiziert=d["verified"])\
            .order_by(desc(Person.zeit)).first()
        new_person = Person(name=d["lastname"], forename=d["firstname"], place=d["location"], verified=d["verified"])
        if emp_old:
            if pers_old:
                n = BullingerDB.get_number_of_differences_from_person(d, pers_old)
                if n:
                    if p_new_query: self.push2db(Empfaenger(id_person=p_new_query.id, remark=d["remarks"]), i, user, t)
                    else:  # new p, new e->p
                        self.push2db(new_person, i, user, t)  # id
                        self.push2db(Empfaenger(id_person=new_person.id, remark=d["remarks"]), i, user, t)
                    if emp_old.bemerkung != d["remarks"].strip(): n += 1
                elif emp_old.bemerkung != d["remarks"].strip():  # comment change only
                    self.push2db(Empfaenger(id_person=pers_old.id, remark=d["remarks"].strip()), i, user, t)
                    n = 1
            else:
                n = 4
                self.push2db(new_person, i, user, t)  # id
                self.push2db(Empfaenger(id_person=new_person.id, remark=d["remarks"].strip()), i, user, t)
        else:
            n = 4
            if p_new_query:
                self.push2db(Empfaenger(id_person=p_new_query.id, remark=d["remarks"].strip()), i, user, t)
            else:
                self.push2db(new_person, i, user, t)  # id
                self.push2db(Empfaenger(id_person=new_person.id, remark=d["remarks"].strip()), i, user, t)
        self.dbs.commit()
        return n

    def save_the_sender(self, i, d, user, t):
        abs_old = Absender.query.filter_by(id_brief=i).order_by(desc(Absender.zeit)).first()
        pers_old = Person.query.filter_by(id=abs_old.id_person).order_by(desc(Person.zeit)).first() if abs_old else None
        p_new_query = Person.query\
            .filter_by(name=d["lastname"], vorname=d["firstname"], ort=d["location"], verifiziert=d["verified"])\
            .order_by(desc(Person.zeit)).first()
        new_person = Person(name=d["lastname"], forename=d["firstname"], place=d["location"], verified=d["verified"])
        if abs_old:
            if pers_old:
                n = BullingerDB.get_number_of_differences_from_person(d, pers_old)
                if n:
                    if p_new_query: self.push2db(Absender(id_person=p_new_query.id, remark=d["remarks"]), i, user, t)
                    else:  # new p, new e->p
                        self.push2db(new_person, i, user, t)  # id
                        self.push2db(Absender(id_person=new_person.id, remark=d["remarks"]), i, user, t)
                    if abs_old.bemerkung != d["remarks"]: n += 1
                elif abs_old.bemerkung != d["remarks"]:  # comment changes only
                    self.push2db(Absender(id_person=pers_old.id, remark=d["remarks"]), i, user, t)
                    n += 1
            else:
                n = 4
                self.push2db(new_person, i, user, t)  # id
                self.push2db(Absender(id_person=new_person.id, remark=d["remarks"]), i, user, t)
        else:
            n = 4
            if p_new_query:
                self.push2db(Absender(id_person=p_new_query.id, remark=d["remarks"]), i, user, t)
            else:
                self.push2db(new_person, i, user, t)  # id
                self.push2db(Absender(id_person=new_person.id, remark=d["remarks"]), i, user, t)
        return n

    def save_copy(self, i, d, user, t):
        copy_old, n = Kopie.query.filter_by(id_brief=i).order_by(desc(Kopie.zeit)).first(), 0
        if copy_old:
            new_copy, n = BullingerDB.update_copy(d, copy_old)
            self.push2db(new_copy, i, user, t)
        elif d["location"] or d["signature"] or d["remarks"]:
            self.push2db(Kopie(standort=d["location"], signatur=d["signature"], umfang=d["remarks"]), i, user, t)
            n = 3
        return n

    @staticmethod
    def update_copy(d, copy_old):
        new_copy, n = Kopie(), 0
        if copy_old.standort != d["location"]: n += 1
        new_copy.standort = d["location"]
        if copy_old.signatur != d["signature"]: n += 1
        new_copy.signatur = d["signature"]
        if copy_old.bemerkung != d["remarks"]: n += 1
        new_copy.bemerkung = d["remarks"]
        return (new_copy, n) if n > 0 else (None, 0)

    def save_literature(self, i, literature, user, t):
        literatur_old, n = Literatur.query.filter_by(id_brief=i).order_by(desc(Literatur.zeit)).first(), 0
        if literatur_old:
            new_literatur, n = BullingerDB.update_literature(literature, literatur_old)
            self.push2db(new_literatur, i, user, t)
        elif literature:
            self.push2db(Literatur(literature=literature), i, user, t)
            n = 1
        return n

    @staticmethod
    def update_literature(literature, literatur_old):
        new_literatur, n = Literatur(literature=literature), 0
        new_literatur.literatur = literature
        if literatur_old.literatur != literature: n += 1
        return (new_literatur, n) if n > 0 else (False, 0)

    def save_language(self, i, lang, user, t):
        lang_entry, n = Sprache.query.filter_by(id_brief=i).order_by(desc(Sprache.zeit)).first(), 0
        if lang_entry:
            language_records = Sprache.query\
                .filter_by(id_brief=i).filter_by(zeit=lang_entry.zeit).order_by(desc(Sprache.zeit)).all()
            new_sprachen, n = BullingerDB.update_language(lang, language_records)
            if new_sprachen:
                for s in new_sprachen: self.push2db(s, i, user, t)
        elif lang:
            for s in BullingerDB.split_lang(lang): self.push2db(Sprache(language=s), i, user, t)
            n += 1
        return n

    @staticmethod
    def update_language(lang, lang_records):
        s_old = [s.sprache for s in lang_records if s.sprache]
        s_new = BullingerDB.split_lang(lang)
        new_languages = []
        if not set(s_old) == set(s_new):
            for s in s_new: new_languages.append(Sprache(language=s.strip()))
            if len(s_new) is 0: new_languages.append(Sprache(language=''))
            return new_languages, len(s_new) - len(set(s_old).intersection(set(s_new)))
        return None, 0

    @staticmethod
    def split_lang(form_entry):
        if form_entry:
            if ";" in form_entry: langs = form_entry.split(";")
            elif "," in form_entry: langs = form_entry.split(",")
            else: langs = form_entry.split("/")
        else: langs = []
        return [l.strip() for l in langs]

    def save_printed(self, i, printed, user, t):
        gedruckt_old, n = Gedruckt.query.filter_by(id_brief=i).order_by(desc(Gedruckt.zeit)).first(), 0
        if gedruckt_old:
            new_gedruckt, n = BullingerDB.update_printed(printed, gedruckt_old)
            self.push2db(new_gedruckt, i, user, t)
        elif printed:
            self.push2db(Gedruckt(printed=printed), i, user, t)
            n = 1
        return n

    @staticmethod
    def update_printed(printed, gedruckt_old):
        new_printed, c = Gedruckt(printed=printed), 0
        if gedruckt_old.gedruckt != printed: c += 1
        return (new_printed, c) if c > 0 else (False, 0)

    def save_remark(self, i, sentence, user, t):
        sentence_old, n = Bemerkung.query.filter_by(id_brief=i).order_by(desc(Bemerkung.zeit)).first(), 0
        if sentence_old:
            new_bemerkung, n = BullingerDB.update_sentence(sentence, sentence_old)
            self.push2db(new_bemerkung, i, user, t)
        elif sentence:
            self.push2db(Bemerkung(remark=sentence), i, user, t)
            n = 1
        return n

    @staticmethod
    def update_sentence(sentence, sentence_old):
        new_sentence, c = Bemerkung(remark=sentence), 0
        if sentence_old.bemerkung != sentence: c += 1
        return (new_sentence, c) if c > 0 else (None, 0)

    def save_comment_card(self, i, note, user, t):
        if note: self.push2db(Notiz(notiz=note), i, user, t)

    @staticmethod
    def get_comments_card(i, user):
        comments = []
        for c in Notiz.query.filter(Notiz.id_brief == i).order_by(asc(Notiz.zeit)).all():
            datum, zeit = re.sub(r'\.\d*', '', c.zeit).split(' ')
            u = "Sie" if c.anwender == user else User.query.filter(anwender=user).id
            comments += [[u, datum, zeit, c.notiz]]
        return comments

    @staticmethod
    def get_comments(user_name):
        comments = []
        for r in Notiz.query.filter(Notiz.id_brief == 0).order_by(asc(Notiz.zeit)).all():
            datum, zeit = re.sub(r'\.\d*', '', r.zeit).split(' ')
            if r.anwender == "Gast": u = "Gast"
            elif r.anwender == ADMIN: u = "Admin"
            elif r.anwender == user_name: u = user_name
            else: u = "Mitarbeiter " + str(User.query.filter_by(username=r.anwender).first().id)
            comments += [[u, datum, zeit, r.notiz]]
        return comments

    @staticmethod
    def save_comment(comment, user_name, t):
        if comment:
            db.session.add(Notiz(id_brief=0, notiz=comment, user=user_name, time=t))
            db.session.commit()

    def push2db(self, db_record, id_brief, user, time_stamp):
        if db_record:
            db_record.id_brief = id_brief
            db_record.anwender = user
            db_record.zeit = time_stamp
            self.dbs.add(db_record)
            self.dbs.commit()

    # other queries
    @staticmethod
    def get_most_recent_only(database, relation):
        sub_query = database.query(
            relation.id_brief,
            func.max(relation.zeit).label('max_date')
        ).group_by(relation.id_brief).subquery('t2')
        query = database.query(relation).join(
            sub_query,
            and_(relation.id_brief == sub_query.c.id_brief,
                 relation.zeit == sub_query.c.max_date)
        )
        return query

    # Overviews
    @staticmethod
    def get_data_overview(year):
        """ yearly: number of letters and their state """
        [n_letters, n_open, n_unclear, n_closed, n_invalid], file_id, c, p = BullingerDB.get_status_counts(year)
        data, sd = [], []
        for key in n_letters:
            if isinstance(key, int):
                data.append([key, n_letters[key], n_open[key], n_unclear[key], n_closed[key], n_invalid[key]])
            else: sd.append([key, n_letters[key], n_open[key], n_unclear[key], n_closed[key], n_invalid[key]])
        return sd+sorted(data, key=itemgetter(0)), file_id, c, p

    @staticmethod
    def get_status_counts(year):
        """ yearly overview """
        recent_dates = BullingerDB.get_most_recent_only(db.session, Datum)
        view_count = CountDict()  # year or month --> letter count
        unclear_count, closed_count, invalid_count, open_count = CountDict(), CountDict(), CountDict(), CountDict()
        for d in recent_dates:
            if not year: view_count.add(d.jahr_a)
            elif str(d.jahr_a) == year: view_count.add(d.monat_a)
        recent_dates = recent_dates.subquery()
        join_file_date = db.session.query(
            Kartei.id_brief,
            Kartei.status,
            recent_dates.c.jahr_a,
            recent_dates.c.monat_a
        ).join(recent_dates, recent_dates.c.id_brief == Kartei.id_brief)
        for r in join_file_date:
            if not year: i = r.jahr_a
            else:
                if str(r.jahr_a) != year: continue
                i = r.monat_a
            if r.status == 'abgeschlossen': closed_count.add(i)
            if r.status == 'unklar': unclear_count.add(i)
            if r.status == 'ungültig': invalid_count.add(i)
            if r.status == 'offen': open_count.add(i)
        o = sum([open_count[c] for c in open_count])
        a = sum([closed_count[c] for c in closed_count])
        u = sum([unclear_count[c] for c in unclear_count])
        i = sum([invalid_count[c] for c in invalid_count])
        file_id = str(int(time.time()))
        PieChart.create_plot_overview_stats(file_id, [o, a, u, i], L_PROGRESS, C_PROGRESS)
        data_stats = BullingerDB.get_status_evaluation(o, a, u, i)
        return [view_count, open_count, unclear_count, closed_count, invalid_count], file_id, data_stats[0], data_stats[1]

    @staticmethod
    def get_data_overview_month(year, month):
        data = []
        for d in Datum.query.filter_by(jahr_a=year, monat_a=month):
            r = Kartei.query.filter_by(id_brief=d.id_brief).first().rezensionen
            s = Kartei.query.filter_by(id_brief=d.id_brief).first().status
            dot_or_not = '.' if d.tag_a != SD else ''
            date = str(d.tag_a) + dot_or_not + ' ' + d.monat_a + ' ' + str(d.jahr_a)
            data.append([d.id_brief, date, r, s])
        cd = CountDict()
        for row in data: cd.add(row[3])
        file_id = year + '_' + month + '_' + str(int(time.time()))
        c, p = BullingerDB.get_status_evaluation(cd["offen"], cd["abgeschlossen"], cd["unklar"], cd["ungültig"])
        PieChart.create_plot_overview_stats(file_id, [cd["offen"], cd["abgeschlossen"], cd["unklar"], cd["ungültig"]], L_PROGRESS, C_PROGRESS)
        return data, file_id, c, p

    @staticmethod
    def get_status_evaluation(o, a, u, i):
        """ :return: [<int>: total number of cards; <dict>: state <str> -> [count <int>, percentage <float>] """
        data, number_of_cards = dict(), sum([o, a, u, i])
        data["offen"] = [o, round(100*o/number_of_cards, 3)]
        data["abgeschlossen"] = [a, round(100*a/number_of_cards, 3)]
        data["unklar"] = [u, round(100*u/number_of_cards, 3)]
        data["ungültig"] = [i, round(100*i/number_of_cards, 3)]
        return [number_of_cards, data]

    @staticmethod
    def quick_start():  # ">>"
        """ return the first card with status 'offen'; if there is none anymore, return cards with state 'unklar'"""
        e = Kartei.query.filter_by(status='offen').first()
        if e: return e.id_brief
        e = Kartei.query.filter_by(status='unklar').first()
        if e: return e.id_brief
        return None  # redirect to another page...

    # Navigation between assignments
    @staticmethod
    def get_next_card_number(i):  # ">"
        """ next card in order """
        return i+1 if i+1 <= Kartei.query.count() else 1

    @staticmethod
    def get_prev_card_number(i):  # "<"
        return i-1 if i-1 > 0 else Kartei.query.count()

    @staticmethod
    def get_prev_assignment(i):  # "<<"
        """ prev open (/unclear, if #open is 0) """
        i, j = BullingerDB.get_prev_card_number(i), Kartei.query.count()
        while not BullingerDB.is_assignable(i) and j > 0:
            i = BullingerDB.get_prev_card_number(i)
            j -= 1
        return i if BullingerDB.is_assignable(i) else None

    @staticmethod
    def get_next_assignment(i):  # ">>"
        i, j = BullingerDB.get_next_card_number(i), Kartei.query.count()
        while not BullingerDB.is_assignable(i) and j > 0:
            i = BullingerDB.get_next_card_number(i)
            j -= 1
        return i if BullingerDB.is_assignable(i) else None

    @staticmethod
    def is_assignable(i):
        c = Kartei.query.filter_by(id_brief=i).filter(or_(Kartei.status == 'offen', Kartei.status == 'unklar')).first()
        return True if c else False

    # Stats/Plots
    @staticmethod
    def get_user_stats_all(user_name):
        table = User.query.order_by(desc(User.changes)).all()
        return [[row.id if user_name != row.username else user_name, row.changes, row.finished] for row in table]

    @staticmethod
    def get_user_stats(user_name):
        u = User.query.filter_by(username=user_name).first()
        if u: return u.changes, u.finished
        else: return 0, 0

    @staticmethod
    def get_language_stats():
        cd, data, no_lang = CountDict(), [], 0
        for s in Sprache.query.all():
            cd.add(s.sprache)
        n = Kartei.query.count()
        for s in cd: data.append([s, cd[s], round(cd[s]/n*100, 3)])
        # for i in range(n+1):  # too expensive ...
        #    if not Sprache.query.filter_by(id_brief=i).first(): no_lang += 1
        # data.append(['-', no_lang, no_lang/n*100, 3])
        return sorted(data, key=itemgetter(1))

    @staticmethod
    def create_plot_lang(data, file_name):
        fig = plt.figure()
        labels = [d[0] for d in data]
        sizes = [d[1] for d in data]
        colors = sample(all_colors, len(sizes))
        patches, texts = plt.pie(sizes, colors=colors, shadow=True, startangle=90)
        plt.legend(patches, labels, loc="best")
        plt.axis('equal')
        plt.tight_layout()
        fig.savefig('App/static/images/plots/lang_stats_'+file_name+'.png')
        plt.close()

    @staticmethod
    def create_plot_user_stats(user_name, file_name):
        fig = plt.figure()
        dc = [(u.changes, 1 if u.username == user_name else 0) for u in User.query.order_by(asc(User.changes)).all()]
        co = ["darkgreen" if u.username == user_name else "dodgerblue" for u in User.query.order_by(asc(User.changes)).all()]
        # changes
        x = ('' if not c[1] else user_name for c in dc)
        x_pos = np.arange(len(dc))
        y = [c[0] for c in dc]
        plt.barh(x_pos, y, align='center', alpha=0.5, color=co)
        plt.yticks(x_pos, x)
        plt.xlabel('Änderungen')
        fig.savefig('App/static/images/plots/user_stats_changes_'+file_name+'.png')
        plt.close()

        # finished
        fig = plt.figure()
        dc = [(u.finished, 1 if u.username == user_name else 0) for u in User.query.order_by(asc(User.finished)).all()]
        co = ["darkgreen" if u.username == user_name else "dodgerblue" for u in User.query.order_by(asc(User.finished)).all()]
        x = ('' if not c[1] else user_name for c in dc)
        x_pos = np.arange(len(dc))
        y = [c[0] for c in dc]
        plt.barh(x_pos, y, align='center', alpha=0.5, color=co)
        plt.yticks(x_pos, x)
        plt.xlabel('abgeschlossen')
        fig.savefig('App/static/images/plots/user_stats_finished_'+file_name+'.png')
        plt.close()

    @staticmethod
    def get_stats_sent_received(limit_s, limit_r):
        ds = [[p.name, p.vorname, p.gesendet] for p in Person.query.order_by(desc(Person.gesendet)).all()]
        dr = [[p.name, p.vorname, p.empfangen] for p in Person.query.order_by(desc(Person.empfangen)).all()]
        return ds[0:limit_s+1], dr[0:limit_r+1]
