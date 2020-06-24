#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# forms.py
# Bernard Schroffenegger
# 20th of October, 2019

""" data exchange server/browser for file cards """

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from App.models import User


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
    submit = SubmitField('Registrieren')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.strip()).first()
        if user is not None: raise ValidationError('existiert bereits')

    def validate_email(self, e_mail):
        user = User.query.filter_by(e_mail=e_mail.data.strip()).first()
        if user is not None: raise ValidationError('existiert bereits')


class GuestBookForm(FlaskForm):

    comment = StringField("Ihre Bemerkung")
    save = SubmitField('Speichern')


class ReferenceForm(FlaskForm):

    reference = StringField("Referenz")
    submit = SubmitField('Speichern')


class PersonNameForm(FlaskForm):

    p_name = StringField('Name')
    p_forename = StringField('Vorname')
    a_name = StringField('Name')
    a_forename = StringField('Vorname')
    submit = SubmitField('Speichern')


class HiddenDataForm(FlaskForm):

    data = StringField('data')
