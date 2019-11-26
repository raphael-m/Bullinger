#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# user.py
# Bernard Schroffenegger
# 29th of October, 2019

from flask_login import AnonymousUserMixin


class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.username = 'Gast'
