#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# forms.py
# Bernard Schroffenegger
# 20th of October, 2019

""" data exchange server/browser for file cards """

from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField, RadioField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from App.models import User, Datum, Autograph, Kopie, Literatur, Gedruckt, Bemerkung, Sprache

IDC = "card__"  # prefix for form IDs


class FormFileCard(FlaskForm):

    # Buttons
    submit = SubmitField('Speichern', id="save_changes")
    next_card = SubmitField('>')  # one card forward
    prev_card = SubmitField('<')  # one card back
    qs_next_card = SubmitField('>>')  # next card (offen/unklar)
    qs_prev_card = SubmitField('<<')  # prev card (offen/unklar)
    state = RadioField('Label', default='unklar',
                       choices=[('unklar', 'unklar'), ('ungültig', 'ungültig'), ('abgeschlossen', 'abgeschlossen')])
    save_comment = SubmitField('Anmerkung speichern')

    # Properties
    image_height = HiddenField('image_height', id="image_height_value")  # window height
    img_height = HiddenField('img_height', id="img_height")  # image size
    img_width = HiddenField('img_width', id="img_width")

    # DATE
    _NSD = "date_"  # namespace
    year_a = StringField("Jahr A", id=IDC + _NSD + "year_a")
    month_a = None
    day_a = StringField("Tag A", id=IDC + _NSD + "day_a")
    year_b = StringField("Jahr B", id=IDC + _NSD + "year_b")
    month_b = None
    day_b = StringField("Tag B", id=IDC + _NSD + "day_b")
    remark_date = StringField("Bemerkung zum Datum", id=IDC + _NSD + "remark")

    def set_date_as_default(self, date):
        """ :param date: database entry """
        self.year_a.default = 's.d.'  # overwrite regular defaults
        self.day_a.default = 's.d.'
        if date:
            self.year_a.default = date.jahr_a if date.jahr_a else 's.d.'
            self.month_a = create_date_selection(date.monat_a)
            self.day_a.default = date.tag_a if date.tag_a else 's.d.'
            self.year_b.default = date.jahr_b if date.jahr_b and date.jahr_b != 's.d.' else ''
            self.month_b = create_date_selection(date.monat_b)
            self.day_b.default = date.tag_b if date.tag_b and date.tag_b != 's.d.' else ''
            self.remark_date.default = date.bemerkung if date.bemerkung else ''

    def update_date(self, datum_old):
        new_datum, number_of_changes = Datum(), 0
        if str(datum_old.jahr_a) != self.year_a.data: number_of_changes += 1  # year/month/day (A)
        new_datum.jahr_a = 's.d.' if not self.year_a.data else self.year_a.data
        if datum_old.monat_a != request.form['card_month_a']: number_of_changes += 1
        new_datum.monat_a = request.form['card_month_a']
        if str(datum_old.tag_a) != self.day_a.data: number_of_changes += 1
        new_datum.tag_a = 's.d.' if not self.day_a.data else self.day_a.data
        if str(datum_old.jahr_b) != self.year_b.data: number_of_changes += 1  # year/month/day (B)
        new_datum.jahr_b = self.year_b.data
        if datum_old.monat_b != request.form['card_month_b']: number_of_changes += 1
        new_datum.monat_b = request.form['card_month_b']
        if str(datum_old.tag_b) != self.day_b.data: number_of_changes += 1
        new_datum.tag_b = self.day_b.data
        if datum_old.bemerkung != self.remark_date.data: number_of_changes += 1  # remark
        new_datum.bemerkung = self.remark_date.data
        if number_of_changes > 0:
            self.set_date_as_default(new_datum)
            return new_datum, number_of_changes
        return None, 0

    _NSS = "sender_"
    name_sender = StringField("Name", id=IDC + _NSS + "name")
    forename_sender = StringField("Vorname", id=IDC + _NSS + "forename")
    place_sender = StringField("Ort", id=IDC + _NSS + "place")
    remark_sender = StringField("Bemerkung", id=IDC + _NSS + "remark")
    sender_verified = RadioField('Absender verifiziert', default='Ja',
                       choices=[('Ja', 'Ja'), ('Nein', 'Nein')])

    def differs_from_sender(self, person):
        n = 0
        if person.name != self.name_sender.data.strip(): n += 1
        if person.vorname != self.forename_sender.data.strip(): n += 1
        if person.ort != self.place_sender.data.strip(): n += 1
        if person.verifiziert != self.sender_verified.data: n += 1
        return n

    def has_changed__sender_comment(self, receiver):
        return True if receiver.bemerkung != self.remark_receiver else False

    def set_sender_as_default(self, person, remark):
        if person:
            self.name_sender.default = person.name if person.name else ''
            self.forename_sender.default = person.vorname if person.vorname else ''
            self.place_sender.default = person.ort if person.ort else ''
            self.sender_verified.default = person.verifiziert if person.verifiziert else 'Nein'
        self.remark_sender.default = remark if remark else ''

    _NSR = "receiver_"
    name_receiver = StringField("Name", id=IDC + _NSR + "name")
    forename_receiver = StringField("Vorname", id=IDC + _NSR + "forename")
    place_receiver = StringField("Ort", id=IDC + _NSR + "place")
    remark_receiver = StringField("Bemerkung", id=IDC + _NSR + "remark")
    receiver_verified = RadioField('Empfänger verifiziert', default='Ja',
                       choices=[('Ja', 'Ja'), ('Nein', 'Nein')])

    def differs_from_receiver(self, person):
        differences = 0
        if person.name != self.name_receiver.data.strip(): differences += 1
        if person.vorname != self.forename_receiver.data.strip(): differences += 1
        if person.ort != self.place_receiver.data.strip(): differences += 1
        if person.verifiziert != self.receiver_verified.data: differences += 1
        return differences

    def has_changed__receiver_comment(self, receiver):
        return True if receiver.bemerkung != self.remark_receiver else False

    def set_receiver_as_default(self, person, remark):
        if person:
            self.name_receiver.default = person.name if person.name else ''
            self.forename_receiver.default = person.vorname if person.vorname else ''
            self.place_receiver.default = person.ort if person.ort else ''
            self.receiver_verified.default = person.verifiziert if person.verifiziert else 'Nein'
        self.remark_receiver.default = remark if remark else ''

    _NSA = "autograph_"
    place_autograph = StringField("Standort", id=IDC + _NSA + "standort")
    signature_autograph = StringField("Signatur", id=IDC + _NSA + "signatur")
    scope_autograph = StringField("Umfang", id=IDC + _NSA + "umfang")

    def set_autograph_as_default(self, autograph):
        if autograph:
            if autograph.standort: self.place_autograph.default = autograph.standort
            if autograph.signatur: self.signature_autograph.default = autograph.signatur
            if autograph.bemerkung: self.scope_autograph.default = autograph.bemerkung

    def update_autograph(self, autograph_old):
        new_autograph, number_of_changes = Autograph(), 0
        if autograph_old.standort != self.place_autograph.data: number_of_changes += 1
        new_autograph.standort = self.place_autograph.data
        if autograph_old.signatur != self.signature_autograph.data: number_of_changes += 1
        new_autograph.signatur = self.signature_autograph.data
        if autograph_old.bemerkung != self.scope_autograph.data: number_of_changes += 1
        new_autograph.bemerkung = self.scope_autograph.data
        if number_of_changes > 0:
            self.set_autograph_as_default(new_autograph)
            return new_autograph, number_of_changes
        return None, 0

    _NSC = "copy_"
    place_copy = StringField("Ort", id=IDC + _NSC + "standort")
    signature_copy = StringField("Signatur", id=IDC + _NSC + "signatur")
    scope_copy = StringField("Bemerkung", id=IDC + _NSC + "Bemerkung")

    def set_copy_as_default(self, copy):
        if copy:
            if copy.standort: self.place_copy.default = copy.standort
            if copy.signatur: self.signature_copy.default = copy.signatur
            if copy.bemerkung: self.scope_copy.default = copy.bemerkung

    def update_copy(self, copy_old):
        new_copy, number_of_changes = Kopie(), 0
        if copy_old.standort != self.place_copy.data: number_of_changes += 1
        new_copy.standort = self.place_copy.data
        if copy_old.signatur != self.signature_copy.data: number_of_changes += 1
        new_copy.signatur = self.signature_copy.data
        if copy_old.bemerkung != self.scope_copy.data: number_of_changes += 1
        new_copy.bemerkung = self.scope_copy.data
        if number_of_changes > 0:
            self.set_copy_as_default(new_copy)
            return new_copy, number_of_changes
        return None, 0

    language = StringField("Sprache", id=IDC + "language_")
    literature = StringField("Literatur", id=IDC + "literature_")
    printed = StringField("Gedruckt", id=IDC + "printed_")
    sentence = StringField("Erster Satz", id=IDC + "sentence_")
    remark = StringField("Bemerkung", id=IDC + "remark_")

    def set_language_as_default(self, sprache):
        if sprache:
            sprachen = [s.sprache for s in sprache if s.sprache]
            if len(sprachen) > 0:
                s = "; ".join(sprachen)
                self.language.default = s
        else:
            self.language.default = ''

    def split_lang(self, form_entry):
        if ";" in form_entry:
            return form_entry.split(";")
        elif "," in form_entry:
            return form_entry.split(",")
        else:
            return form_entry.split("/")

    def update_language(self, sprache_old):
        number_of_changes = 0
        s_old = [s.sprache for s in sprache_old if s.sprache]
        s_new = self.split_lang(self.language.data)
        new_languages = []
        if not set(s_old) == set(s_new):
            number_of_changes += (len(s_new) - len(s_old)) if len(s_old) < len(s_new) else (len(s_old) - len(s_new))
            for s in s_new:
                new_languages.append(Sprache(language=s))
            self.set_language_as_default(new_languages)
            return new_languages, number_of_changes
        return None, 0

    def set_literature_as_default(self, literatur):
        if literatur:
            self.literature.default = literatur.literatur if literatur.literatur else ''
            print("setted")

    def update_literature(self, literatur_old):
        print("OLD", literatur_old, "NEW", self.literature.data)
        new_literatur, number_of_changes = Literatur(), 0
        if literatur_old.literatur != self.literature.data: number_of_changes += 1
        new_literatur.literatur = self.literature.data
        if number_of_changes > 0:
            print("change")
            self.set_literature_as_default(new_literatur)
            return new_literatur, number_of_changes
        return False, 0

    def set_printed_as_default(self, gedruckt):
        if gedruckt:
            self.printed.default = gedruckt.gedruckt if gedruckt.gedruckt else ''

    def update_printed(self, gedruckt_old):
        number_of_changes = 0
        new_printed = Gedruckt()
        if gedruckt_old.gedruckt != self.printed.data: number_of_changes += 1
        new_printed.gedruckt = self.printed.data
        if number_of_changes > 0:
            self.set_printed_as_default(new_printed)
            return new_printed, number_of_changes
        return False, 0

    def set_sentence_as_default(self, sentence):
        if sentence:
            self.sentence.default = sentence.bemerkung if sentence.bemerkung else ''

    def update_sentence(self, sentence_old):
        number_of_changes = 0
        new_sentence = Bemerkung()
        if sentence_old.bemerkung != self.sentence.data: number_of_changes += 1
        new_sentence.bemerkung = self.sentence.data
        if number_of_changes > 0:
            self.set_sentence_as_default(new_sentence)
            return new_sentence, number_of_changes
        return False, 0

    def set_remark_as_default(self, remark):
        pass

    note = TextAreaField("Benutzerkommentar", id=IDC + "note")


def create_date_selection(selection):
    date = {
        "s.d.": True,
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
        if selection in date:
            date[selection] = True
        else:
            date["s.d."] = True
    return date


class LoginForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    remember_me = BooleanField('angemeldet bleiben')
    submit = SubmitField('Anmelden')


class RegistrationForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    password2 = PasswordField('Passwort (Wiederholung)', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('existiert bereits')

    def validate_email(self, e_mail):
        user = User.query.filter_by(e_mail=e_mail.data).first()
        if user is not None:
            raise ValidationError('existiert bereits')
