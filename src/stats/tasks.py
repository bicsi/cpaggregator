from cpaggregator.celery import app
from .services import compute_task_statistics, compute_user_statistics


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Compute statistics.
    sender.add_periodic_task(
        5, # * 60,
        compute_user_statistics,
        name='compute user statistics')
    sender.add_periodic_task(
        5, # * 60,
        compute_task_statistics,
        name='compute task statistics')

print('HAI PIZDA')
print(app.conf.beat_schedule)