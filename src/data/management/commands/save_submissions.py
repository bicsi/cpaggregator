from django.core.management.base import BaseCommand

from scraper.database import get_db
from data.models import Submission
import json


class Compressor(object):
    values = 0
    data = {}

    def get(self, id):
        if id not in self.data:
            self.data[id] = self.values
            self.values += 1
        return self.data[id]


class Command(BaseCommand):
    help = 'Updates the users with submissions for the available tasks.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-o', '--outfile',
            dest='outfile',
            metavar='FILE',
            required=True,
            help='write output to FILE json')

    def handle_mongo(self, *args, **options):
        db = get_db()

        task_compressor = Compressor()

        submission_map = {}
        for submission in db['submissions'].find().sort('submitted_on', 1):
            task_id = task_compressor.get(submission['task_id'])
            author_id = submission['author_id']
            solved = (submission['verdict'] == 'AC')
            if author_id not in submission_map:
                submission_map[author_id] = []
            submission_map[author_id].append({
                'task_id': task_id,
                'solved': solved,
            })

        dataset = [{'author_id': author_id, 'submissions': submission_map[author_id]}
                   for author_id in submission_map]
        tasks = [{'task_name': task_name, 'task_id': task_id}
                 for task_name, task_id in task_compressor.data.items()]

        json_data = {
            'dataset': dataset,
            'tasks': tasks,
        }

        output_file = options['outfile']
        with open(output_file, 'w') as fout:
            json.dump(json_data, fout, sort_keys=True, indent=4)

    def handle(self, *args, **options):
        return self.handle_mongo(*args, **options)

        submission_map = {}
        for submission in Submission.best.order_by('submitted_on'):
            task_id = submission.task.id
            author_id = submission.author.user.id
            solved = (submission.verdict == 'AC')
            if author_id not in submission_map:
                submission_map[author_id] = []
            submission_map[author_id].append({
                'task_id': task_id,
                'solved': solved,
            })

        json_data = [{'author_id': author_id, 'submissions': submission_map[author_id]}
                     for author_id in submission_map]

        output_file = options['outfile']
        with open(output_file, 'w') as fout:
            json.dump(json_data, fout, sort_keys=True, indent=4)
