import os
from celery import Celery
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'problem_service.settings')

app = Celery('problem_service')
app.conf.broker_url = 'amqp://guest:guest@rabbitmq:5672//'
app.conf.result_backend = 'redis://redis:6379/0'


app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60, 
    task_soft_time_limit=25 * 60,  
)

app.autodiscover_tasks()