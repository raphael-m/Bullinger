#!/bin/bash
#reset_server.sh

git pull || git reset --hard origin/master

pkill gunicorn

sudo systemctl stop nginx
sudo supervisorctl stop all
sudo service supervisor reload
sudo service nginx restart

gunicorn -w 33 App:app