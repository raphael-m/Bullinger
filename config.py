#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# config.py
# Bernard Schroffenegger
# 20th of October, 2019

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'the010gy_sucks:P'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BULLINGER_UI_PATH = os.environ.get('BULLINGER_UI_PATH') or 'http://bullinger.raphaelm.ch/'

    # status cards
    S_OPEN = 'offen'
    S_UNKNOWN = 'unklar'
    S_FINISHED = 'abgeschlossen'
    S_INVALID = 'ungültig'

    # null values
    SD = 's.d.'
