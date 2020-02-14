#!/bin/bash
#reset_server.sh

rm App/static/images/plots/*.png

git pull || git reset --hard origin/master

pkill gunicorn

sudo systemctl stop nginx
sudo supervisorctl stop all
sudo service supervisor reload
sudo service nginx restart

gunicorn -w 33 App:app