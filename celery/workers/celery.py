from celery import Celery
from celery.schedules import crontab
from workers.schedules.tasks.video_task import sync_sqs_logs
import os
from dotenv import load_dotenv

load_dotenv()

CELERY_BROKER = os.environ.get('CELERY_BROKER_SCHEME') + '://' + \
                os.environ.get('CELERY_BROKER_HOST') + ':' + \
                os.environ.get('CELERY_BROKER_PORT') + '/' + \
                os.environ.get('CELERY_BROKER_DB')

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
