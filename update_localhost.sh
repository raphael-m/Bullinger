#!/bin/bash
#localhost_update.sh

bash Scripts/localhost_db_fetch.sh
bash Scripts/localhost_push.sh $1
