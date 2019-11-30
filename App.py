#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# App.py
# Bernard Schroffenegger
# 20th of October, 2019

from App import app

HOST = 'localhost'
PORT = 5000
DEBUG = True


if __name__ == '__main__':

    app.run(debug=DEBUG, host=HOST, port=PORT)
