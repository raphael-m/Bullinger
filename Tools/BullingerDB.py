#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# BullingerData.py
# Bernard Schroffenegger
# 30th of November, 2019

from Tools.BullingerData import *
from Tools.NGrams import NGrams
from App.models import *
from sqlalchemy import desc

ADMIN = 'Admin'


class BullingerDB(db):

    t = datetime.now()

    def add_bullinger(self):
        bullinger = Person(name="Bullinger", title="", forename="Heinrich", place="Zürich", user=ADMIN, time=self.t)
        self.add(bullinger)
        self.commit()

    @staticmethod
    def get_id_bullinger():
        return Person.query.filter_by(name="Bullinger").order_by(desc(Person.zeit)).first().id

    def add_date(self, card_nr, data):
        date = BullingerData.extract_date(card_nr, data)
        if not date:
            date = Datum(id_brief=card_nr, year_a=SD, month_a=SD, day_a=SD)
        date.user, data.time = ADMIN, self.t
        self.add(date)

    def add_correspondents(self, card_nr, data):
        """ one has to be bullinger """
        n_grams_bullinger = NGrams.get_dicts_bullinger(4)
        id_bullinger = BullingerDB.get_id_bullinger()
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

    def add_remark(self, card_nr, data):
        remark = BullingerData.get_remark(data)
        if remark:
            self.add(Bemerkung(id_brief=card_nr, remark=remark, user=ADMIN, time=self.t))
            return remark
        return ''

    def add_lang(self, card_nr, data, remark):
        for lang in BullingerData.get_lang(data, remark):
            self.add(Sprache(id_brief=card_nr, language=lang, user=ADMIN, time=self.t))

    @staticmethod
    def setup(dir_path):
        d, card_nr = BullingerDB(), 0
        d.add_bullinger()
        for path in FileSystem.get_file_paths(dir_path, recursively=False):
            card_nr += 1
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
            d.commit()
