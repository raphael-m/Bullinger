#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# forms.py
# Bernard Schroffenegger
# 20th of October, 2019

""" data exchange server/browser for file cards """

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField, RadioField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from App.models import User

IDC = "card__"  # prefix for form IDs


class FormFileCard(FlaskForm):

    # Buttons
    submit = SubmitField('Speichern', id="save_changes")
    submit_and_next = SubmitField('Speichern & Weiter')
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

    def set_default_state(self, state):
        self.state.default = state.status if state else ''

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

    _NSS = "sender_"
    name_sender = StringField("Name", id=IDC + _NSS + "name")
    forename_sender = StringField("Vorname", id=IDC + _NSS + "forename")
    place_sender = StringField("Ort", id=IDC + _NSS + "place")
    remark_sender = StringField("Bemerkung", id=IDC + _NSS + "remark")
    sender_verified = RadioField('Absender verifiziert', default='Ja',
                       choices=[('Ja', 'Ja'), ('Nein', 'Nein')])

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

    _NSC = "copy_"
    place_copy = StringField("Ort", id=IDC + _NSC + "standort")
    signature_copy = StringField("Signatur", id=IDC + _NSC + "signatur")
    scope_copy = StringField("Bemerkung", id=IDC + _NSC + "Bemerkung")

    def set_copy_as_default(self, copy):
        if copy:
            if copy.standort: self.place_copy.default = copy.standort
            if copy.signatur: self.signature_copy.default = copy.signatur
            if copy.bemerkung: self.scope_copy.default = copy.bemerkung

    language = StringField("Sprache", id=IDC + "language_")
    literature = StringField("Literatur", id=IDC + "literature_")
    printed = StringField("Gedruckt", id=IDC + "printed_")
    sentence = StringField("Erster Satz", id=IDC + "sentence_")
    remark = StringField("Bemerkung", id=IDC + "remark_")

    def set_language_as_default(self, records):
        if records:
            sprachen = [s.sprache for s in records if s.sprache]
            if len(sprachen) > 0:
                s = "; ".join(sprachen)
                self.language.default = s
        else: self.language.default = ''

    def set_literature_as_default(self, literatur):
        if literatur: self.literature.default = literatur.literatur if literatur.literatur else ''

    def set_printed_as_default(self, gedruckt):
        if gedruckt: self.printed.default = gedruckt.gedruckt if gedruckt.gedruckt else ''

    def set_sentence_as_default(self, sentence):
        if sentence: self.sentence.default = sentence.bemerkung if sentence.bemerkung else ''

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
        if selection in date:
            date[selection] = True
            date["s.d."] = False
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
        user = User.query.filter_by(username=username.data.strip()).first()
        if user is not None:
            raise ValidationError('existiert bereits')

    def validate_email(self, e_mail):
        user = User.query.filter_by(e_mail=e_mail.data.strip()).first()
        if user is not None:
            raise ValidationError('existiert bereits')


class FormComments(FlaskForm):
    comment = StringField("Kommentar")
    save = SubmitField('Speichern')
