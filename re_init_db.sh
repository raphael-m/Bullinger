#!/bin/bash
#restart_server.sh

rm -rf migrations

rm app.db
touch app.db

flask db init
flask db migrate -m "initializing fresh db"
flask db upgrade
