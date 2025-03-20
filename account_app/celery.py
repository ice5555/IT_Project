import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'account_app.settings')

app = Celery('account_app')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
