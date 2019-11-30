#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# BullingerDB.py
# Bernard Schroffenegger
# 30th of November, 2019

import os
from Tools.BullingerData import *
from Tools.NGrams import NGrams
from App.models import *
from sqlalchemy import desc
from flask import request

ADMIN = 'Admin'


class BullingerDB(db.session):

    t = datetime.now()

    @staticmethod
    def setup(dir_path):
        """ creates the entire date base (ocr data) """
        d, card_nr = BullingerDB(), 1
        d.delete_all()
        d.set_index()
        d.add_bullinger()
        for path in FileSystem.get_file_paths(dir_path, recursively=False):
            print(card_nr, path)
            data = BullingerData.get_data_as_dict(path)
            if data:
                d.add_date(card_nr, data)
                d.add_correspondents(card_nr, data)
                d.add_autograph(card_nr, data)
                d.add_copy(card_nr, data)
                d.add_literature(card_nr, data)
                d.add_printed(card_nr, data)
                remark = db.add_remark(card_nr, data)
                d.add_lang(card_nr, data, remark)
            else:
                print("*** WARNING, file ignored:", path)
                d.add(Datum(id_brief=card_nr, year_a=SD, month_a=SD, day_a=SD, user=ADMIN, time=d.t))
            card_nr += 1
            d.commit()
        d.count_correspondence()

    def set_index(self):
        # self.session.query(Kartei).delete()
        for i in range(1, 10094):
            zeros = (5 - len(str(i))) * '0'
            pdf = os.path.join("Karteikarten/PDF", "HBBW_Karteikarte_" + zeros + str(i) + ".pdf")
            ocr = os.path.join("Karteikarten/OCR", "HBBW_Karteikarte_" + zeros + str(i) + ".ocr")
            self.add(Kartei(id_brief=i, pfad_pdf=pdf, pfad_ocr=ocr))
        self.commit()

    def delete_all(self):
        self.query(User).delete()
        self.query(Kartei).delete()
        self.query(Datum).delete()
        self.query(Person).delete()
        self.query(Absender).delete()
        self.query(Empfaenger).delete()
        self.query(Autograph).delete()
        self.query(Kopie).delete()
        self.query(Sprache).delete()
        self.query(Literatur).delete()
        self.query(Gedruckt).delete()
        self.query(Bemerkung).delete()
        self.commit()

    def update_file_status(self, id_brief, state):
        file = Kartei.query.filter_by(id_brief=id_brief).first()
        file.status = state
        file.rezensionen += 1
        self.commit()

    def update_user(self, user, number_of_changes):
        user = User.query.filter_by(username=user).first()
        user.changes += number_of_changes
        self.commit()

    def add_bullinger(self):
        bullinger = Person(name="Bullinger", title="", forename="Heinrich", place="Zürich", user=ADMIN, time=self.t)
        self.add(bullinger)
        self.commit()

    def add_date(self, card_nr, data):
        date = BullingerData.extract_date(card_nr, data)
        if not date:
            date = Datum(id_brief=card_nr, year_a=SD, month_a=SD, day_a=SD)
        date.user, data.time = ADMIN, self.t
        self.add(date)

    def add_correspondents(self, card_nr, data):
        """ one has to be bullinger """
        n_grams_bullinger = NGrams.get_dicts_bullinger(4)
        id_bullinger = Person.query.filter_by(name="Bullinger").order_by(desc(Person.zeit)).first().id
        if BullingerData.is_bullinger_sender(data, n_grams_bullinger):
            self.add(Absender(id_brief=card_nr, id_person=id_bullinger, user=ADMIN, time=self.t))
            e = BullingerData.analyze_address(data["Empfänger"])
            match = Person.query.filter_by(name=e[0], vorname=e[1], titel=e[4], ort=e[2]).first()
            if not match:
                self.add(Person(title=e[4], name=e[0], forename=e[1], place=e[2], user=ADMIN, time=self.t))
                self.commit()
            ref = Person.query.filter_by(name=e[0], vorname=e[1], titel=e[4], ort=e[2]).first().id
            self.add(Empfaenger(id_brief=card_nr, id_person=ref, remark=e[3], user=ADMIN, time=self.t))
        else:
            self.add(Empfaenger(id_brief=card_nr, id_person=id_bullinger, user=ADMIN, time=self.t))
            a = BullingerData.analyze_address(data["Absender"])
            match = Person.query.filter_by(name=a[0], vorname=a[1], ort=a[2], titel=a[4]).first()
            if not match:
                self.add(Person(title=a[4], name=a[0], forename=a[1], place=a[2], user=ADMIN, time=self.t))
                self.commit()
            ref = Person.query.filter_by(name=a[0], vorname=a[1], ort=a[2], titel=a[4]).first().id
            self.add(Absender(id_brief=card_nr, id_person=ref, remark=a[3], user=ADMIN, time=self.t))

    def add_autograph(self, card_nr, data):
        place, signature, scope = BullingerData.get_ssu(data, "A")
        if place or signature:
            a = Autograph(id_brief=card_nr, standort=place, signatur=signature, umfang=scope, user=ADMIN, time=self.t)
            self.add(a)

    def add_copy(self, card_nr, data):
        place, signature, scope = BullingerData.get_ssu(data, "B")
        if place or signature:
            k = Kopie(id_brief=card_nr, standort=place, signatur=signature, umfang=scope, user=ADMIN, time=self.t)
            self.add(k)

    def add_literature(self, card_nr, data):
        literature = BullingerData.get_literature(data)
        if literature:
            self.add(Literatur(id_brief=card_nr, literature=literature, user=ADMIN, time=self.t))

    def add_printed(self, card_nr, data):
        printed = BullingerData.get_printed(data)
        if printed:
            self.add(Gedruckt(id_brief=card_nr, printed=printed, user=ADMIN, time=self.t))

    def add_lang(self, card_nr, data, remark):
        for lang in BullingerData.get_lang(data, remark):
            self.add(Sprache(id_brief=card_nr, language=lang, user=ADMIN, time=self.t))

    def add_remark(self, card_nr, data):
        remark = BullingerData.get_remark(data)
        if remark:
            self.add(Bemerkung(id_brief=card_nr, remark=remark, user=ADMIN, time=self.t))
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
        form.set_language_as_default([s for s in sprache if s.zeit == sprache.first().zeit])
        form.set_printed_as_default(Gedruckt.query.filter_by(id_brief=id_).order_by(desc(Gedruckt.zeit)).first())
        form.set_sentence_as_default(Bemerkung.query.filter_by(id_brief=id_).order_by(desc(Bemerkung.zeit)).first())
        return [datum.jahr_a, datum.monat_a, datum.tag_a]

    def count_correspondence(self):
        for e in Empfaenger.query.all():
            p = Person.query.get(e.id_person)
            p.empfangen = p.empfangen+1 if p.empfangen else 1
        for a in Absender.query.all():
            p = Person.query.get(a.id_person)
            p.gesendet = p.gesendet+1 if p.gesendet else 1
        self.commit()

    def print_correspondence_count(self):
        df = pd.read_sql(db.session.query(Person).statement, db.session.bind)
        df = df.loc[:, "name":"gesendet"]
        df = df.fillna(0)
        df.gesendet, df.empfangen = df.gesendet.astype(int), df.empfangen.astype(int)
        df_e = df.sort_values(by=['empfangen'], ascending=False)
        df_a = df.sort_values(by=['gesendet'], ascending=False)
        e, a = df_e.to_latex(index=False), df_a.to_latex(index=False)
        print(a, "\n", e)

    '''
    def query_wrongly_identified_bullingers():
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
        
        """
        89 Karten
        ---------
        [864, 3483, 2066, 2783, 4254, 5788, 6079, 6159, 6429, 6698, 6742, 6846, 6969, 7008, 7013, 7070, 7093, 7112,
        7126, 7144, 7244, 7285, 7296, 7403, 7460, 7479, 7505, 7603, 7632, 7634, 7684, 7706, 7734, 7744, 7800, 7841,
        7848, 8268, 8279, 8384, 8437, 8438, 8567, 8712, 8724, 8749, 8756, 8801, 8814, 8845, 8857, 8871, 8928, 9000,
        9003, 9018, 9019, 9022, 9034, 9039, 9059, 9083, 9085, 9110, 9113, 9121, 9122, 9132, 9199, 9249, 9285, 9286,
        9290, 9328, 9354, 9521, 9571, 9580, 9608, 9609, 9661, 9665, 9716, 9815, 9848, 9863, 9928, 9934, 9944]
        """
    '''

    def save_date(self, i, card_form, user, t):
        datum_old, n = Datum.query.filter_by(id_brief=i).order_by(desc(Datum.zeit)).first(), 0
        if datum_old:
            new_date, n_changes = card_form.update_date(datum_old)
            n += n_changes
            if new_date:
                new_date.id_brief = i
                new_date.anwender = user
                new_date.zeit = t
                self.add(new_date)
        else:  # date doesn't exist yet (this should never be the case)
            db.session.add(Datum(id_brief=i,
                year_a=card_form.year_a.data, month_a=request.form['card_month_a'], day_a=card_form.day_a.data,
                year_b=card_form.year_b.data, month_b=request.form['card_month_b'], day_b=card_form.day_b.data,
                remark=card_form.remark.data, user=user, time=t))
            n += 7
        self.commit()
        return n

    def save_autograph(self, i, card_form, user, t):
        autograph_old, n = Autograph.query.filter_by(id_brief=i).order_by(desc(Autograph.zeit)).first(), 0
        if autograph_old:
            new_autograph, n_changes = card_form.update_autograph(autograph_old)
            n += n_changes
            if new_autograph:
                new_autograph.id_brief = i
                new_autograph.anwender = user
                new_autograph.zeit = t
                self.add(new_autograph)
        else:
            db.session.add(Autograph(id_brief=i, standort=card_form.place_autograph.data,
                                     signatur=card_form.signature_autograph.data, umfang=card_form.scope_autograph.data,
                                     user=user, time=t))
            n += 3
        self.commit()
        return n

    def save_sender(self, i, card_form, user, t):
        emp_old, n = Empfaenger.query.filter_by(id_brief=i).order_by(desc(Empfaenger.zeit)).first(), 0
        pers_old = Person.query.filter_by(id=emp_old.id_person).order_by(desc(Person.zeit)).first()
        p_new_query = Person.query.filter_by(titel=card_form.title_receiver.data,
                                             name=card_form.name_receiver.data,
                                             vorname=card_form.forename_receiver.data,
                                             ort=card_form.place_receiver.data).order_by(desc(Person.zeit)).first()
        new_person = Person(title=card_form.title_receiver.data, name=card_form.name_receiver.data,
                            forename=card_form.forename_receiver.data, place=card_form.place_receiver.data,
                            user=user, time=t)
        if emp_old:
            if pers_old:
                changes = card_form.differs_from_receiver(pers_old)
                if n:
                    n += changes
                    if p_new_query:  # p_new well known ==> (r_new -> p)
                        self.add(Empfaenger(id_brief=i, id_person=p_new_query.id, remark=card_form.remark_receiver.data,
                                            user=user, time=t))
                    else:  # new p, new e->p
                        self.add(new_person)
                        self.commit()  # id
                        self.add(Empfaenger(id_brief=i, id_person=new_person.id, remark=card_form.remark_receiver.data,
                                            user=user, time=t))
                else:  # comment changes only
                    if card_form.has_changed__receiver_comment(emp_old):
                        self.add(Empfaenger(id_brief=i, id_person=pers_old.id, remark=card_form.remark_receiver.data,
                                            user=user, time=t))
                        n += 1
            else:
                self.add(new_person)
                self.commit()  # id
                self.add(Empfaenger(id_brief=i, id_person=new_person.id, remark=card_form.remark_receiver.data,
                                    user=user, time=t))
                n += 4
        else:
            if p_new_query:
                self.add(Empfaenger(id_brief=i, id_person=p_new_query.id, remark=card_form.remark_receiver.data,
                                          user=user, time=t))
            else:
                self.add(new_person)
                self.commit()  # id
                self.add(Empfaenger(id_brief=i, id_person=new_person.id, remark=card_form.remark_receiver.data,
                                    user=user, time=t))
            n += 4
        self.commit()
        if n:
            card_form.set_receiver_as_default(new_person, card_form.remark_receiver.data)
        return n

    def save_receiver(self, i, card_form, user, t):
        abs_old, n = Absender.query.filter_by(id_brief=i).order_by(desc(Absender.zeit)).first(), 0
        pers_old = Person.query.filter_by(id=abs_old.id_person).order_by(desc(Person.zeit)).first()
        p_new_query = Person.query.filter_by(titel=card_form.title_sender.data, name=card_form.name_sender.data,
                                             vorname=card_form.forename_sender.data, ort=card_form.place_sender.data)\
                                             .order_by(desc(Person.zeit)).first()
        new_person = Person(title=card_form.title_sender.data, name=card_form.name_sender.data,
                            forename=card_form.forename_sender.data, place=card_form.place_sender.data,
                            user=user, time=t)
        if abs_old:
            if pers_old:
                changes = card_form.differences_from_sender(pers_old)
                if n:
                    n += changes
                    if p_new_query:  # p_new well known ==> (r_new -> p)
                        self.add(Absender(id_brief=i, id_person=p_new_query.id, remark=card_form.remark_sender.data,
                                          user=user, time=t))
                    else:  # new p, new e->p
                        self.add(new_person)
                        self.commit()  # id
                        self.add(Absender(id_brief=i, id_person=new_person.id, remark=card_form.remark_sender.data,
                                          user=user, time=t))
                else:  # comment changes only
                    if card_form.has_changed__sender_comment(abs_old):
                        self.add(Absender(id_brief=i, id_person=pers_old.id, remark=card_form.remark_sender.data,
                                          user=user, time=t))
                        n += 1
            else:
                self.add(new_person)
                self.commit()  # id
                self.add(Absender(id_brief=i, id_person=new_person.id, remark=card_form.remark_sender.data,
                                  user=user, time=t))
                n += 4
        else:
            if p_new_query:
                self.add(Absender(id_brief=i, id_person=p_new_query.id, remark=card_form.remark_sender.data,
                                  user=user, time=t))
            else:
                self.add(new_person)
                self.commit()  # id
                self.add(Absender(id_brief=i, id_person=new_person.id, remark=card_form.remark_sender.data,
                                  user=user, time=t))
        self.commit()
        if n:
            card_form.set_sender_as_default(new_person, card_form.remark_sender.data)
        return n

    def save_copy(self, i, card_form, user, t):
        copy_old, n = Kopie.query.filter_by(id_brief=i).order_by(desc(Kopie.zeit)).first(), 0
        if copy_old:
            new_copy, n_changes = card_form.update_copy(copy_old)
            n += n_changes
            if new_copy:
                new_copy.id_brief = i
                new_copy.anwender = user
                new_copy.zeit = t
                self.add(new_copy)
        else:
            self.add(Kopie(id_brief=i, standort=card_form.place_copy.data, signatur=card_form.signature_copy.data,
                           umfang=card_form.scope_copy.data, user=user, time=t))
            n += 3
        self.commit()
        return n

    def save_literature(self, i, card_form, user, t):
        literatur_old, n = Literatur.query.filter_by(id_brief=i).order_by(desc(Literatur.zeit)).first(), 0
        if literatur_old:
            new_literatur, n_changes = card_form.update_literature(literatur_old)
            n += n_changes
            if new_literatur:
                new_literatur.id_brief = i
                new_literatur.anwender = user
                new_literatur.zeit = t
                self.add(new_literatur)
        else:
            self.add(Literatur(id_brief=i, literature=card_form.literature.data, user=user, time=t))
            n += 1
        self.commit()
        return n

    def save_language(self, i, card_form, user, t):
        sprache_old, n = Sprache.query.filter_by(id_brief=i).order_by(desc(Sprache.zeit)).first(), 0  # most recent
        sprache_old = Sprache.query.filter_by(id_brief=i).filter_by(zeit=sprache_old.zeit).order_by(desc(Sprache.zeit))
        if sprache_old:
            new_sprachen, n_changes = card_form.update_language(sprache_old)
            n += n_changes
            if not new_sprachen:
                self.add(Sprache(id_brief=i, language='', user=user, time=t))
            else:
                for s in new_sprachen:
                    s.id_brief = i
                    s.anwender = user
                    s.zeit = t
                    self.add(s)
        else:
            for s in card_form.split_lang(card_form.language.data):
                self.add(Sprache(id_brief=i, language=s, user=user, time=t))
                n += 1
        self.commit()
        sprache = Sprache.query.filter_by(id_brief=i).order_by(desc(Sprache.zeit))
        card_form.set_language_as_default([s for s in sprache if s.zeit == sprache.first().zeit])
        return n

    def save_printed(self, i, card_form, user, t):
        gedruckt_old, n = Gedruckt.query.filter_by(id_brief=i).order_by(desc(Gedruckt.zeit)).first(), 0
        if gedruckt_old:
            new_gedruckt, n_changes = card_form.update_printed(gedruckt_old)
            if new_gedruckt:
                new_gedruckt.id_brief = i
                new_gedruckt.anwender = user
                new_gedruckt.zeit = t
                self.add(new_gedruckt)
        else:
            self.add(Gedruckt(id_brief=i, printed=card_form.printed.data, user=user, time=t))
            n += 1
        self.commit()
        return n

    def save_remark(self, i, card_form, user, t):
        sentence_old, n = Bemerkung.query.filter_by(id_brief=i).order_by(desc(Bemerkung.zeit)).first(), 0
        if sentence_old:
            new_bemerkung, n_changes = card_form.update_sentence(sentence_old)
            n += n_changes
            if new_bemerkung:
                new_bemerkung.id_brief = i
                new_bemerkung.anwender = user
                new_bemerkung.zeit = t
                self.add(new_bemerkung)
        else:
            self.add(Bemerkung(id_brief=i, remark=card_form.sentence.data, user=user, time=t))
            n += 1
        self.commit()
        return n
