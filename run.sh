# !/bin/bash
source /home/ubuntu/miniconda3/etc/profile.d/conda.sh
conda activate VocabHelper
celery -A account_app worker --loglevel=info
celery -A account_app beat --loglevel=info
tmux new-session -s gunicorn_session_2 'gunicorn --workers 1 account_app.wsgi:application --bind 0.0.0.0:5555'






