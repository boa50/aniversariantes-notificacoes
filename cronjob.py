from apscheduler.schedulers.blocking import BlockingScheduler

from main import process_notifications

scheduler = BlockingScheduler()
scheduler.add_job(process_notifications, 'cron', hour='0', minute='30', second='0', jitter=120)

scheduler.start()