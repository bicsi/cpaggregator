import math

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from pymongo import MongoClient

from data import models
from data.models import User, Submission, Task, Judge

DATABASE_NAME = 'competitive'


def _update_user(db, username):
    print("Updating %s..." % username)

    user = User.objects.get(username=username)
    for user_handle in user.userhandle_set.all():
        judge = user_handle.judge
        # Get all submissions from mongodb.
        mongo_submissions = db['submissions'].find(dict(
            judge_id=judge.judge_id,
            author_id=user_handle.handle,
        ))
        # Migrate submission model to SQL model.
        for mongo_submission in mongo_submissions:
            try:
                task = Task.objects.get(
                    judge=judge,
                    task_id=mongo_submission['task_id'],
                )

                update_dict = dict(
                    submitted_on=mongo_submission['submitted_on'],
                    author=user_handle,
                    verdict=mongo_submission['verdict'],
                    language=mongo_submission.get('language'),
                    source_size=mongo_submission.get('source_size'),
                    score=mongo_submission.get('score'),
                    exec_time=mongo_submission.get('exec_time'),
                    memory_used=mongo_submission.get('memory_used'),
                )
                if math.isnan(update_dict['score']):
                    update_dict['score'] = None
                update_dict = dict(filter(lambda x: x[1] and x[1], update_dict.items()))

                print(update_dict)

                _, created = Submission.objects.update_or_create(
                    submission_id=mongo_submission['submission_id'],
                    task=task, defaults=update_dict
                )

                if created:
                    print("Submission %s created." % mongo_submission['submission_id'])
                else:
                    print("Submissions %s updated." % mongo_submission['submission_id'])

            except:
                pass


class Command(BaseCommand):
    help = 'Updates the user(s) with submissions for the available tasks.'
    args = '<user1, user2, ...>'

    def add_arguments(self, parser):
        parser.add_argument('users', nargs='+', type=str)

    def handle(self, *args, **options):
        client = MongoClient()
        db = client[DATABASE_NAME]

        for user in User.objects.all():
            _update_user(db, user.username)
        # for username in options['users']:
        #    _update_user(db, username)
