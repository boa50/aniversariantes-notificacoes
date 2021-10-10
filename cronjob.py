from apscheduler.schedulers.blocking import BlockingScheduler

from main import process_notifications

scheduler = BlockingScheduler()
scheduler.add_job(process_notifications, 'cron', second='*/30')

scheduler.start()