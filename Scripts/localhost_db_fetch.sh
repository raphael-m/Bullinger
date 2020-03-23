#!/bin/bash
#localhost_download_server_data.sh

# download the current database
scp ubuntu@130.60.24.72:/home/ubuntu/Bullinger/app.db .
cp app.db Data/DB_Backups/app_$(date "+%Y.%m.%d-%H.%M.%S").db
