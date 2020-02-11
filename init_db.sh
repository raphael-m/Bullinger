#!/bin/bash
#re_init_db.sh

rm -rf migrations

rm app.db
touch app.db

flask db init
flask db migrate -m "new empty database"
flask db upgrade
