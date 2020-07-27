#!/bin/bash
#run.sh

source venv/bin/activate
export FLASK_APP=App.py
export FLASK_ENV=development
FLASK_DEBUG=1
flask run
