from data.models import UserProfile, UserHandle, Task
from .models import ProfileScheduleInfo, TaskScheduleInfo
from django.db.models import F
from core.logging import log
from scraper import services as scraper_services
from django.utils import timezone


def scrape_user_info(to_days=300000, batch_size=5):
    profiles = (UserProfile.objects
                .order_by(F('schedule_info__last_updated_on').asc(nulls_first=True))
                .select_related('schedule_info')[:batch_size])

    for profile in profiles:
        schedule_info, _ = ProfileScheduleInfo.objects.get_or_create(
            profile=profile)
        log.info(
            f'Scraping user info: {profile} (last updated time: {schedule_info.last_updated_on})')
        handles = UserHandle.objects.filter(
            user=profile).select_related('judge').all()

        for handle in handles:
            handle = f"{handle.judge.judge_id}/{handle.handle}"
            log.info(f'Scraping handle info: {handle}')
            scraper_services.scrape_submissions_for_users(
                handle, to_days=to_days)
            scraper_services.scrape_handle_info(handle)

        schedule_info.last_updated_on = timezone.now()
        schedule_info.save()


def scrape_task_submissions(to_days=300000, batch_size=5):
    tasks = (Task.objects
             .order_by(F('schedule_info__last_updated_on').asc(nulls_first=True))
             .select_related('judge')[:batch_size])
    for task in tasks:
        schedule_info, _ = TaskScheduleInfo.objects.get_or_create(
            task=task)
        log.info(
            f'Scraping task submissions: {task} (last updated time: {schedule_info.last_updated_on})')

        task_id = f"{task.judge.judge_id}/{task.task_id}"
        scraper_services.scrape_submissions_for_tasks(
            task_id, to_days=to_days)

        schedule_info.last_updated_on = timezone.now()
        schedule_info.save()
