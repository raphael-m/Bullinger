#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# BullingerDB.py
# Bernard Schroffenegger
# 30th of November, 2019

from Tools.Dictionaries import CountDict
from Tools.Plots import *
from App.models import *
from sqlalchemy import asc, desc, func, and_, or_, literal, union_all
from operator import itemgetter
from random import sample, randrange

import os, time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as pltc

all_colors = [k for k, v in pltc.cnames.items()]
matplotlib.use('agg')

ADMIN = 'Admin'  # username (setup)
L_PROGRESS = ["offen", "abgeschlossen", "unklar", "ungültig"]  # labels (plots)
C_PROGRESS = ["navy", "forestgreen", "orange", "red"]


class BullingerDB:

    def __init__(self, database_session):
        self.dbs = database_session
        self.bd = BullingerData(None, None)
        self.t = datetime.now()

    def update_timestamp(self):
        self.t = datetime.now()

    def delete_all(self):
        self.dbs.query(User).delete()
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
        self.dbs.query(Tracker).delete()
        self.dbs.commit()

    def setup(self, dir_path):
        self.delete_all()
        card_nr, num_ignored_cards, ignored_card_ids = 1, 0, []
        id_bullinger = self.add_bullinger()
        for path in FileSystem.get_file_paths(dir_path, recursively=False):
            print(card_nr, path)
            self.update_timestamp()
            self.set_index(card_nr)
            self.bd = BullingerData(path, card_nr)
            if self.bd.get_data():
                self.add_date(card_nr)
                self.add_correspondents(card_nr, id_bullinger)
                self.add_autograph(card_nr)
                self.add_copy(card_nr)
                self.add_literature(card_nr)
                self.add_printed(card_nr)
                self.add_remark(card_nr)
                self.add_lang(card_nr)
            else:
                print("*** WARNING, file ignored:", path)
                self.push2db(Datum(), card_nr, ADMIN, self.t)
                num_ignored_cards += 1
                ignored_card_ids.append(card_nr)
            card_nr += 1
            self.dbs.commit()
        if num_ignored_cards: print("*** WARNING,", num_ignored_cards, "files ignored:", ignored_card_ids)
        BullingerDB.count_correspondence()  # post-processing

    def add_bullinger(self):
        self.dbs.add(Person(name="Bullinger", forename="Heinrich", place="Zürich", user=ADMIN, time=self.t))
        self.dbs.commit()
        return Person.query.filter_by(name="Bullinger", vorname="Heinrich", ort="Zürich").first().id

    def set_index(self, i):
        zeros = (5 - len(str(i))) * '0'
        pdf = os.path.join("Karteikarten/PDF", "HBBW_Karteikarte_" + zeros + str(i) + ".pdf")
        ocr = os.path.join("Karteikarten/OCR", "HBBW_Karteikarte_" + zeros + str(i) + ".ocr")
        self.dbs.add(Kartei(id_brief=i, path_pdf=pdf, path_ocr=ocr, user=ADMIN, time=self.t))
        self.dbs.commit()

    def remove_user(self, username):
        """ delete a user and all its changes """
        self.dbs.query(User).filter_by(username=username).delete()
        for t in [Datum, Person, Absender, Empfaenger, Autograph, Kopie, Sprache, Literatur, Gedruckt, Bemerkung, Notiz]:
            self.dbs.query(t).filter_by(anwender=username).delete()
        self.dbs.commit()

    @staticmethod
    def get_bullinger_number_of_letters():
        b = Person.query.filter_by(name='Bullinger', vorname="Heinrich", ort='Zürich').first()
        return (b.gesendet, b.empfangen) if b else (0, 0)

    def add_date(self, card_nr):
        y, m, d = self.bd.get_date()
        date = Datum(year_a=y, month_a=m, day_a=d)
        self.push2db(date, card_nr, ADMIN, self.t)

    def add_correspondents(self, card_nr, id_bullinger):
        """ one has to be bullinger """
        if self.bd.is_bullinger_sender():
            nn, vn, ort, bem = self.bd.get_receiver()
            self.push2db(Absender(id_person=id_bullinger), card_nr, ADMIN, self.t)
            p = Person.query.filter_by(name=nn, vorname=vn, ort=ort).first()
            if not p: self.push2db(Person(name=nn, forename=vn, place=ort), card_nr, ADMIN, self.t)
            p_id = Person.query.filter_by(name=nn, vorname=vn, ort=ort).first().id  # p.id is None (!)
            self.push2db(Empfaenger(id_brief=card_nr, id_person=p_id, remark=bem), card_nr, ADMIN, self.t)
        else:
            self.push2db(Empfaenger(id_brief=card_nr, id_person=id_bullinger), card_nr, ADMIN, self.t)
            nn, vn, ort, bem = self.bd.get_sender()
            p = Person.query.filter_by(name=nn, vorname=vn, ort=ort).first()
            if not p: self.push2db(Person(name=nn, forename=vn, place=ort), card_nr, ADMIN, self.t)
            p_id = Person.query.filter_by(name=nn, vorname=vn, ort=ort).first().id
            self.push2db(Absender(id_brief=card_nr, id_person=p_id, remark=bem), card_nr, ADMIN, self.t)

    def add_autograph(self, card_nr):
        place, signature, remark = self.bd.get_autograph()
        self.push2db(Autograph(location=place, signature=signature, remark=remark), card_nr, ADMIN, self.t)

    def add_copy(self, card_nr):
        place, signature, remark = self.bd.get_copy()
        self.push2db(Kopie(location=place, signature=signature, remark=remark), card_nr, ADMIN, self.t)

    def add_literature(self, card_nr):
        self.push2db(Literatur(literature=self.bd.get_literature()), card_nr, ADMIN, self.t)

    def add_printed(self, card_nr):
        self.push2db(Gedruckt(printed=self.bd.get_printed()), card_nr, ADMIN, self.t)

    def add_lang(self, card_nr):
        for lang in self.bd.get_sprache(): self.push2db(Sprache(language=lang), card_nr, ADMIN, self.t)
        if not len(self.bd.get_sprache()): self.push2db(Sprache(language=None), card_nr, ADMIN, self.t)

    def add_remark(self, card_nr):
        self.push2db(Bemerkung(remark=self.bd.get_bemerkung()), card_nr, ADMIN, self.t)

    @staticmethod
    def track(username, url, t):
        if username != ADMIN:
            db.session.add(Tracker(username=username, time=t, url=url))
            db.session.commit()

    @staticmethod
    def count_correspondence():
        """ very inefficient, but doesn't matter """
        for e in Empfaenger.query.all():
            p = Person.query.get(e.id_person)
            p.empfangen = p.empfangen + 1 if p.empfangen else 1
        for a in Absender.query.all():
            p = Person.query.get(a.id_person)
            p.gesendet = p.gesendet + 1 if p.gesendet else 1
        db.session.commit()

    def save_date(self, i, data_date, user, t):
        datum_old, n = Datum.query.filter_by(id_brief=i).order_by(desc(Datum.zeit)).first(), 0
        if datum_old:
            new_date, n = BullingerDB.update_date(data_date, datum_old)
            self.push2db(new_date, i, user, t)
        elif data_date["year"] or data_date["month"] or data_date["day"] \
                or data_date["year_b"] or data_date["month_b"] or data_date["day_b"]:
            self.push2db(Datum(
                year_a=None if not data_date["year"] else data_date["year"],
                month_a=None if not data_date["month"] else data_date["month"],
                day_a=None if not data_date["day"] else data_date["day"],
                year_b=None if not data_date["year_b"] else data_date["year_b"],
                month_b=None if not data_date["month_b"] else data_date["month_b"],
                day_b=None if not data_date["day_b"] else data_date["day_b"],
                remark=None if not data_date["remarks"] else data_date["remarks"]
            ), i, user, t)
            n = 7
        return n

    @staticmethod
    def update_date(data_date, datum_old):
        new_datum, n = Datum(), 0  # number of changes
        if datum_old.jahr_a != data_date["year"]: n += 1  # year/month/day (A)
        new_datum.jahr_a = None if not data_date["year"] else data_date["year"]
        if datum_old.monat_a != data_date["month"]: n += 1
        new_datum.monat_a = None if not data_date["month"] else data_date["month"]
        if datum_old.tag_a != data_date["day"]: n += 1
        new_datum.tag_a = None if not data_date["day"] else data_date["day"]
        if datum_old.jahr_b != data_date["year_b"]: n += 1  # year/month/day (B)
        new_datum.jahr_b = None if not data_date["year_b"] else data_date["year_b"]
        if datum_old.monat_b != data_date["month_b"]: n += 1
        new_datum.monat_b = None if not data_date["month_b"] else data_date["month_b"]
        if datum_old.tag_b != data_date["day_b"]: n += 1
        new_datum.tag_b = None if not data_date["day_b"] else data_date["day_b"]
        if datum_old.bemerkung != data_date["remarks"]: n += 1  # remark
        new_datum.bemerkung = None if not data_date["remarks"] else data_date["remarks"]
        return (new_datum, n) if n > 0 else (None, 0)

    def save_autograph(self, i, d, user, t):
        autograph_old, n = Autograph.query.filter_by(id_brief=i).order_by(desc(Autograph.zeit)).first(), 0
        if autograph_old:
            new_autograph, n = BullingerDB.update_autograph(d, autograph_old)
            self.push2db(new_autograph, i, user, t)
        elif d["location"] or d["signature"] or d["remarks"]:
            self.push2db(Autograph(location=d["location"], signature=d["signature"], remark=d["remarks"]), i, user, t)
            n = 3
        self.dbs.commit()
        return n

    @staticmethod
    def update_autograph(d, autograph_old):
        a_new, n = Autograph(), 0
        if autograph_old.standort != d["location"]: n += 1
        a_new.standort = d["location"]
        if autograph_old.signatur != d["signature"]: n += 1
        a_new.signatur = d["signature"]
        if autograph_old.bemerkung != d["remarks"]: n += 1
        a_new.bemerkung = d["remarks"]
        return (a_new, n) if n > 0 else (None, 0)

    @staticmethod
    def get_number_of_differences_from_person(data, person):
        n = 0  # differences
        if person:
            a, b, c = data["lastname"], data["firstname"], data["location"]
            if person.name != (a.strip() if a else a): n += 1
            if person.vorname != (b.strip() if b else b): n += 1
            if person.ort != (c.strip() if c else c): n += 1
        return n

    def save_the_receiver(self, i, d, user, t):
        d["verified"], n = None if not d["verified"] else True, 5
        e_old = Empfaenger.query.filter_by(id_brief=i).order_by(desc(Empfaenger.zeit)).first()
        e_new = Empfaenger(verified=d["verified"], remark=d["remarks"])
        p_old = Person.query.filter_by(id=e_old.id_person).order_by(desc(Person.zeit)).first() if e_old else None
        p_new = Person.query.filter_by(name=d["lastname"], vorname=d["firstname"], ort=d["location"]) \
            .order_by(desc(Person.zeit)).first()
        if not p_new:
            new_person = Person(name=d["lastname"], forename=d["firstname"], place=d["location"])
            self.push2db(new_person, i, user, t)  # id
            e_new.id_person = new_person.id
        else:
            e_new.id_person = p_new.id
        if e_old and p_old:
            n = BullingerDB.get_number_of_differences_from_person(d, p_old)
            if e_old.bemerkung != d["remarks"]: n += 1
            if e_old.verifiziert != d["verified"]: n += 1
            if n > 0: self.push2db(e_new, i, user, t)
        else:
            self.push2db(e_new, i, user, t)
        self.dbs.commit()
        return n

    def save_the_sender(self, i, d, user, t):
        d["verified"], n = None if not d["verified"] else True, 5
        a_old = Absender.query.filter_by(id_brief=i).order_by(desc(Absender.zeit)).first()
        a_new = Absender(verified=d["verified"], remark=d["remarks"])
        p_old = Person.query.filter_by(id=a_old.id_person).order_by(desc(Person.zeit)).first() if a_old else None
        p_new = Person.query.filter_by(name=d["lastname"], vorname=d["firstname"], ort=d["location"]) \
            .order_by(desc(Person.zeit)).first()
        if not p_new:
            new_person = Person(name=d["lastname"], forename=d["firstname"], place=d["location"])
            self.push2db(new_person, i, user, t)  # id
            a_new.id_person = new_person.id
        else:
            a_new.id_person = p_new.id
        if a_old and p_old:
            n = BullingerDB.get_number_of_differences_from_person(d, p_old)
            if a_old.bemerkung != d["remarks"]: n += 1
            if a_old.verifiziert != d["verified"]: n += 1
            if n > 0: self.push2db(a_new, i, user, t)
        else:
            self.push2db(a_new, i, user, t)
        return n

    def save_copy(self, i, d, user, t):
        copy_old, n = Kopie.query.filter_by(id_brief=i).order_by(desc(Kopie.zeit)).first(), 0
        if copy_old:
            new_copy, n = BullingerDB.update_copy(d, copy_old)
            self.push2db(new_copy, i, user, t)
        elif d["location"] or d["signature"] or d["remarks"]:
            self.push2db(Kopie(location=d["location"], signature=d["signature"], remark=d["remarks"]), i, user, t)
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
            language_records = Sprache.query \
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
            if len(s_new) is 0:
                new_languages.append(Sprache(language=None))
            if len(s_new) > len(s_old): n = len(s_new) - len(set(s_old).intersection(set(s_new)))
            if len(s_new) < len(s_old): n = len(s_old) - len(set(s_old).intersection(set(s_new)))
            return new_languages, n
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
        if note: self.push2db(Notiz(note=note), i, user, t)

    @staticmethod
    def get_comments(user_name):
        comments = []
        for r in Notiz.query.filter(Notiz.id_brief == 0).order_by(asc(Notiz.zeit)).all():
            datum, zeit = re.sub(r'\.\d*', '', r.zeit).split(' ')
            if r.anwender == "Gast":
                u = "Gast"
            elif r.anwender == ADMIN:
                u = "Admin"
            elif r.anwender == user_name:
                u = user_name
            else:
                u = "Mitarbeiter " + str(User.query.filter_by(username=r.anwender).first().id)
            comments += [[u, datum, zeit, r.notiz]]
        return comments

    @staticmethod
    def save_comment(comment, user_name, t):
        if comment:
            db.session.add(Notiz(id_brief=0, note=comment, user=user_name, time=t))
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
        return database.query(relation).join(
            sub_query,
            and_(relation.id_brief == sub_query.c.id_brief,
                 relation.zeit == sub_query.c.max_date)
        )

    # Overviews
    @staticmethod
    def _get_data_overview(year=None, state=None):
        y = None if year == Config.SD else year
        recent_index = BullingerDB.get_most_recent_only(db.session, Kartei).subquery()
        recent_dates = BullingerDB.get_most_recent_only(db.session, Datum).subquery()
        base = db.session.query(
            recent_index.c.id_brief,
            recent_index.c.status,
            recent_dates.c.jahr_a,
            recent_dates.c.monat_a
        ).join(recent_dates, recent_dates.c.id_brief == recent_index.c.id_brief)
        if state: base = base.filter(recent_index.c.status == state)
        if year: base = base.filter(recent_dates.c.jahr_a == y)
        col = recent_dates.c.jahr_a if not y else recent_dates.c.monat_a
        null_count = len(base.filter(col.is_(None)).all())
        base = base.subquery()
        col = base.c.jahr_a if not y else base.c.monat_a
        data = dict(db.session.query(col, func.count(col)).group_by(col).all())
        if None in data: del data[None]
        count = sum([data[k] for k in data if data[k]])
        return data, null_count, count+null_count

    @staticmethod
    def get_data_overview(year):
        ya, y0, cy = BullingerDB._get_data_overview(year=year)
        do, do0, co = BullingerDB._get_data_overview(year=year, state='offen')
        da, da0, ca = BullingerDB._get_data_overview(year=year, state='abgeschlossen')
        du, du0, cu = BullingerDB._get_data_overview(year=year, state='unklar')
        di, di0, ci = BullingerDB._get_data_overview(year=year, state='ungültig')
        data_overview = [[[Config.SD, 0], do0, du0, da0, di0]] if y0 else []
        for x in sorted(ya):
            no = do[x] if x in do else 0
            na = da[x] if x in da else 0
            nu = du[x] if x in du else 0
            ni = di[x] if x in di else 0
            val = BullingerDB.convert_month_to_str(x) if year else x
            data_overview.append([[val, x], no, nu, na, ni])
        plot_url = PieChart.create_plot_overview_stats(str(int(time.time())), [co, ca, cu, ci], L_PROGRESS, C_PROGRESS)
        num_of_cards, data_percentages = BullingerDB.get_status_evaluation(co, ca, cu, ci)
        return data_overview, data_percentages, plot_url, num_of_cards

    @staticmethod
    def normalize_str_input(value):
        if not isinstance(value, str): return None
        elif not value.strip(): return None
        else: return value.strip()

    @staticmethod
    def normalize_int_input(value):
        if isinstance(value, int): return value
        elif isinstance(value, str):
            try: return int(value)
            except: return None
        else: return None

    @staticmethod
    def convert_month_to_str(m):
        try: return BullingerDB.convert_month_int2str(int(m))
        except:
            n = BullingerDB._convert_month_str2int(m)
            return BullingerDB.convert_month_int2str(n)

    @staticmethod
    def convert_month_int2str(m):
        try:
            m = int(m)
            switch_dict = {
                1: 'Januar',
                2: 'Februar',
                3: 'März',
                4: 'April',
                5: 'Mai',
                6: 'Juni',
                7: 'Juli',
                8: 'August',
                9: 'September',
                10: 'Oktober',
                11: 'November',
                12: 'Dezember'
            }
            return switch_dict[m] if m in switch_dict else None
        except: return None

    @staticmethod
    def convert_month_to_int(m):
        try: return int(m) if 0 < int(m) < 13 else None
        except: return BullingerDB._convert_month_str2int(m)

    @staticmethod
    def _convert_month_str2int(m):
        # m = str(m)
        switch_dict = {
            'Januar': 1,
            'Februar': 2,
            'März': 3,
            'April': 4,
            'Mai': 5,
            'Juni': 6,
            'Juli': 7,
            'August': 8,
            'September': 9,
            'Oktober': 10,
            'November': 11,
            'Dezember': 12
        }
        return switch_dict[m] if m in switch_dict else None

    @staticmethod
    def get_data_overview_month(year, month):
        year = BullingerDB.normalize_int_input(year)
        m_num = BullingerDB.convert_month_to_int(month)
        data, null = [], []
        for d in Datum.query.filter_by(jahr_a=year, monat_a=m_num):
            recent_index = BullingerDB.get_most_recent_only(db.session, Kartei).filter_by(id_brief=d.id_brief).first()
            r = recent_index.rezensionen
            s = recent_index.status
            if d.tag_a: data.append([d.id_brief, d.tag_a, d.monat_a, d.jahr_a, r, s])
            else: null.append([d.id_brief, d.tag_a, d.monat_a, d.jahr_a, r, s])
        data, new = null + sorted(data, key=itemgetter(1)), []
        for d in data:
            day = str(d[1])+'. ' if d[1] else Config.SD
            mon = BullingerDB.convert_month_to_str(m_num)
            mon = Config.SD if not mon else mon
            y = str(d[3]) if d[3] else Config.SD
            new.append([d[0], [' '.join([day, mon, y]), m_num], d[4], d[5]])
        data = new
        cd = CountDict()
        for row in data+null: cd.add(row[3])
        num_of_cards, data_percentages = BullingerDB.get_status_evaluation(cd["offen"], cd["abgeschlossen"], cd["unklar"], cd["ungültig"])
        plot_url = PieChart.create_plot_overview_stats(str(int(time.time())), [cd["offen"], cd["abgeschlossen"], cd["unklar"], cd["ungültig"]], L_PROGRESS, C_PROGRESS)
        return data, data_percentages, plot_url, num_of_cards

    @staticmethod
    def get_status_evaluation(o, a, u, i):
        """ :return: [<int>: total number of cards; <dict>: state <str> -> [count <int>, percentage <float>] """
        data, number_of_cards = dict(), sum([o, a, u, i])
        if number_of_cards > 0:
            data[Config.S_OPEN] = [o, round(100 * o / number_of_cards, 3)]
            data[Config.S_FINISHED] = [a, round(100 * a / number_of_cards, 3)]
            data[Config.S_UNKNOWN] = [u, round(100 * u / number_of_cards, 3)]
            data[Config.S_INVALID] = [i, round(100 * i / number_of_cards, 3)]
        else:
            data[Config.S_OPEN] = [o, Config.NONE]
            data[Config.S_FINISHED] = [a, Config.NONE]
            data[Config.S_UNKNOWN] = [u, Config.NONE]
            data[Config.S_INVALID] = [i, Config.NONE]
        return [number_of_cards, data]

    @staticmethod
    def quick_start():  # ">>"
        e = BullingerDB.get_cards_with_status(Config.S_OPEN)
        if e: return e[randrange(len(e))].id_brief
        e = BullingerDB.get_cards_with_status(Config.S_UNKNOWN)
        if e: return e[randrange(len(e))].id_brief
        return None  # redirect to another page...

    @staticmethod
    def get_cards_with_status(status):
        recent_index = BullingerDB.get_most_recent_only(db.session, Kartei).subquery().alias("recent_index")
        return db.session.query(
                recent_index.c.id_brief,
                recent_index.c.status
            ).filter(recent_index.c.status == status).all()

    @staticmethod
    def get_number_of_cards():
        return BullingerDB.get_most_recent_only(db.session, Kartei).count()

    # Navigation between assignments
    @staticmethod
    def get_next_card_number(i):  # ">"
        """ next card in order """
        return i + 1 if i + 1 <= BullingerDB.get_number_of_cards() else 1

    @staticmethod
    def get_prev_card_number(i):  # "<"
        return i - 1 if i - 1 > 0 else BullingerDB.get_number_of_cards()

    @staticmethod
    def get_prev_assignment(i):  # "<<"
        """ prev open (/unclear, if #open is 0) """
        i, j = BullingerDB.get_prev_card_number(i), BullingerDB.get_number_of_cards()
        while not BullingerDB.is_assignable(i) and j > 0:
            i = BullingerDB.get_prev_card_number(i)
            j -= 1
        return i if BullingerDB.is_assignable(i) else None

    @staticmethod
    def get_next_assignment(i):  # ">>"
        i, j = BullingerDB.get_next_card_number(i), BullingerDB.get_number_of_cards()
        while not BullingerDB.is_assignable(i) and j > 0:
            i = BullingerDB.get_next_card_number(i)
            j -= 1
        return i if BullingerDB.is_assignable(i) else None

    @staticmethod
    def is_assignable(i):
        recent_index = BullingerDB.get_most_recent_only(db.session, Kartei).subquery().alias("recent_index")
        c = db.session.query(
                recent_index.c.id_brief,
                recent_index.c.status
            ).filter(recent_index.c.id_brief == i)\
            .filter(or_(
                recent_index.c.status == 'offen',
                recent_index.c.status == 'unklar')
            ).first()
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
        for s in Sprache.query.all(): cd.add(s.sprache)
        n = BullingerDB.get_number_of_cards()
        data = [[s if s else Config.NONE, cd[s], round(cd[s] / n * 100, 3)] for s in cd]
        return sorted(data, key=itemgetter(1), reverse=True)

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
        fig.savefig('App/static/images/plots/lang_stats_' + file_name + '.png')
        plt.close()

    @staticmethod
    def create_plot_user_stats(user_name, file_name):
        fig = plt.figure()
        dc = [(u.changes, 1 if u.username == user_name else 0) for u in User.query.order_by(asc(User.changes)).all()]
        co = ["darkgreen" if u.username == user_name else "dodgerblue" for u in
              User.query.order_by(asc(User.changes)).all()]
        # changes
        x = ('' if not c[1] else user_name for c in dc)
        x_pos = np.arange(len(dc))
        y = [c[0] for c in dc]
        plt.barh(x_pos, y, align='center', alpha=0.5, color=co)
        plt.yticks(x_pos, x)
        plt.xlabel('Änderungen')
        fig.savefig('App/static/images/plots/user_stats_changes_' + file_name + '.png')
        plt.close()

        # finished
        fig = plt.figure()
        dc = [(u.finished, 1 if u.username == user_name else 0) for u in User.query.order_by(asc(User.finished)).all()]
        co = ["darkgreen" if u.username == user_name else "dodgerblue" for u in
              User.query.order_by(asc(User.finished)).all()]
        x = ('' if not c[1] else user_name for c in dc)
        x_pos = np.arange(len(dc))
        y = [c[0] for c in dc]
        plt.barh(x_pos, y, align='center', alpha=0.5, color=co)
        plt.yticks(x_pos, x)
        plt.xlabel('abgeschlossen')
        fig.savefig('App/static/images/plots/user_stats_finished_' + file_name + '.png')
        plt.close()

    @staticmethod
    def get_top_n_sender(n):
        p = Person.query.order_by(desc(Person.gesendet)).all()
        if n > len(p): n = len(p)
        return [[x.name if x.name else Config.SN,
                 x.vorname if x.vorname else Config.SN,
                 x.ort if x.ort else Config.SL, x.gesendet] for x in p][0:n]

    @staticmethod
    def get_top_n_receiver(n):
        p = Person.query.order_by(desc(Person.empfangen)).all()
        if n > len(p): n = len(p)
        return [[x.name if x.name else Config.SN,
                 x.vorname if x.vorname else Config.SN,
                 x.ort if x.ort else Config.SL, x.empfangen] for x in p][0:n]

    @staticmethod
    def get_top_n_sender_ignoring_place(n):
        p = db.session.query(Person.name, Person.vorname, func.sum(Person.gesendet))\
            .group_by(Person.name, Person.vorname)\
            .order_by(desc(func.sum(Person.gesendet))).all()
        if n > len(p): n = len(p)
        return [[x[0] if x[0] else Config.SN,
                 x[1] if x[1] else Config.SN, x[2]] for x in p][0:n]

    @staticmethod
    def get_top_n_receiver_ignoring_place(n):
        p = db.session.query(Person.name, Person.vorname, func.sum(Person.empfangen))\
            .group_by(Person.name, Person.vorname)\
            .order_by(desc(func.sum(Person.empfangen))).all()
        if n > len(p): n = len(p)
        return [[x[0] if x[0] else Config.SN,
                 x[1] if x[1] else Config.SN, x[2]] for x in p][0:n]

    @staticmethod
    def get_persons_by_var(variable, mode):
        """ mode=0: variable=Name
            mode=1: variable=Vorname
            mode=2: variable=Ort
            return [[brief_id, nn, vn, ort, rezensionen, status], ...] """
        recent_sender = BullingerDB.get_most_recent_only(db.session, Absender).subquery()
        recent_receiver = BullingerDB.get_most_recent_only(db.session, Empfaenger).subquery()
        # sender
        p1 = db.session.query(
                Person.id.label("p_id_a"),
                Person.name.label("p_name"),
                Person.vorname.label("p_forename"),
                Person.ort.label("p_place"),
                func.count(Person.id).label("s_count"),
                literal(0).label("r_count"),
                recent_sender.c.id_brief.label("id_a"),
                recent_sender.c.id_person.label("p_id_b"))\
            .filter(
                Person.name == variable if mode is 0
                else Person.vorname == variable if mode is 1
                else Person.ort == variable if mode is 2
                else True)\
            .join(recent_sender, recent_sender.c.id_person == Person.id) \
            .group_by(Person.name, Person.vorname, Person.ort)
        # receiver
        p2 = db.session.query(
                Person.id.label("p_id_a"),
                Person.name.label("p_name"),
                Person.vorname.label("p_forename"),
                Person.ort.label("p_place"),
                literal(0).label("s_count"),
                func.count(Person.id).label("r_count"),
                recent_receiver.c.id_brief.label("id_a"),
                recent_receiver.c.id_person.label("p_id_b"))\
            .filter(
                Person.name == variable if mode is 0
                else Person.vorname == variable if mode is 1
                else Person.ort == variable if mode is 2
                else True)\
            .join(recent_receiver, recent_receiver.c.id_person == Person.id)\
            .group_by(Person.name, Person.vorname, Person.ort)
        # full outer join and sum over groups
        p_all = union_all(p1, p2).alias("united")
        results = db.session.query(
                p_all.c.p_name,
                p_all.c.p_forename,
                p_all.c.p_place,
                func.sum(p_all.c.s_count),
                func.sum(p_all.c.r_count)
            ).group_by(
                p_all.c.p_name,
                p_all.c.p_forename,
                p_all.c.p_place
            ).order_by(desc(func.sum(p_all.c.s_count)))
        return [[r[0] if r[0] else Config.SN,
                 r[1] if r[1] else Config.SN,
                 r[2] if r[2] else Config.SL, r[3], r[4]] for r in results]

    @staticmethod
    def get_overview_person(name, forename, place):
        recent_sender = BullingerDB.get_most_recent_only(db.session, Absender).subquery()
        recent_receiver = BullingerDB.get_most_recent_only(db.session, Empfaenger).subquery()
        # sender
        p1 = db.session.query(
                Person.id.label("p_id_a"),
                Person.name.label("p_name"),
                Person.vorname.label("p_forename"),
                Person.ort.label("p_place"),
                recent_sender.c.id_person.label("p_id_b"),
                recent_sender.c.id_brief.label("id_a"))\
            .filter(Person.name == name)\
            .filter(Person.vorname == forename)\
            .filter(Person.ort == place)\
            .join(recent_sender, recent_sender.c.id_person == Person.id)
        # receiver
        p2 = db.session.query(
                Person.id.label("p_id_a"),
                Person.name.label("p_name"),
                Person.vorname.label("p_forename"),
                Person.ort.label("p_place"),
                recent_receiver.c.id_person.label("p_id_b"),
                recent_receiver.c.id_brief.label("id_a"))\
            .filter(Person.name == name)\
            .filter(Person.vorname == forename)\
            .filter(Person.ort == place)\
            .join(recent_receiver, recent_receiver.c.id_person == Person.id)
        p_all = union_all(p1, p2).alias("united")
        results = db.session.query(
            p_all.c.id_a,
            p_all.c.p_name,
            p_all.c.p_forename,
            p_all.c.p_place,
        ).order_by(desc(p_all.c.id_a))
        return [[r[0],
                 r[1] if r[1] else Config.SN,
                 r[2] if r[2] else Config.SN,
                 r[3] if r[3] else Config.SL] for r in results]

    @staticmethod
    def get_overview_languages(lang):
        data = db.session.query(
                Sprache.id_brief,
                Sprache.sprache
            ).filter(Sprache.sprache == lang)\
            .order_by(asc(Sprache.id_brief))
        return [[d.id_brief, d.sprache if d.sprache else Config.NONE] for d in data]

    @staticmethod
    def get_number_of_page_visits():
        n = Tracker.query.count()
        t0 = Tracker.query.order_by(asc(Tracker.time)).first()
        if t0:
            t0 = datetime.strptime(t0.time, "%Y-%m-%d %H:%M:%S.%f")
            tf = "%d.%m.%Y, %H:%M:%S"
            t = t0.strftime(tf)
            return n, t
        return n, '-'
