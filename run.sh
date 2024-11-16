# !/bin/bash

source /home/ubuntu/miniconda3/etc/profile.d/conda.sh
conda activate evshare

tmux new-session -s gunicorn_session 'gunicorn --workers 1 account_app.wsgi:application --bind 127.0.0.1:5555'