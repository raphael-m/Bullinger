#!/bin/bash
#restart_server.sh

source venv/bin/activate

pip freeze > requirements.txt
pip install -r requirements.txt

git pull || git reset --hard origin/master

pkill gunicorn

sudo systemctl stop nginx
sudo supervisorctl stop all
sudo service supervisor reload
sudo service nginx restart

gunicorn -w 33 App:app
