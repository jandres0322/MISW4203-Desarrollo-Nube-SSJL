from celery import shared_task
from api.services.process import read_messages_queue

@shared_task(name='sync_sqs_logs', bind=True, max_retries=2)
def sync_sqs_logs(self):
    try:
        read_messages_queue(self)

    except Exception as e:
        raise self.retry(exc=e)
