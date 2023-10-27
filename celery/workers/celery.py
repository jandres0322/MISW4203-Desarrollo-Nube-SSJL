from celery import Celery
from celery.schedules import crontab
from workers.schedules.tasks.video_task import sync_sqs_logs
import os

CELERY_BROKER = os.environ.get('CELERY_URL', 'redis://redis:6379/0')
celery_app = Celery('app', broker=CELERY_BROKER, backend=CELERY_BROKER, broker_connection_retry_on_startup=True )
celery_app.autodiscover_tasks(['workers.schedules.tasks.video_task'])
celery_app.conf.beat_schedule = {
    'sync_sqs_logs': {
        'task': 'sync_sqs_logs',
        'schedule': crontab(minute='*/1'),
        'args': ()
    },
}

celery_app.conf.timezone = 'America/Bogota'
