# !/bin/bash

source /home/ubuntu/miniconda3/etc/profile.d/conda.sh
conda activate VocabHelper

tmux new-session -s gunicorn_session 'gunicorn --workers 1 account_app.wsgi:application --bind 127.0.0.1:5555'

tmux new-session -s gunicorn_session_2 'gunicorn --workers 1 account_app.wsgi:application --bind 0.0.0.0:5555'



celery -A account_app worker --loglevel=info
celery -A account_app beat --loglevel=info