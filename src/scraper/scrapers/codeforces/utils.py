import datetime
import heapq

from scraper.utils import get_page
import json

CODEFORCES_JUDGE_ID = 'cf'


def __parse_verdict(verdict_text):
    verdict_dict = {
        'OK': 'AC',
        'COMPILATION_ERROR': 'CE',
        'RUNTIME_ERROR': 'RE',
        'TIME_LIMIT_EXCEEDED': 'TLE',
        'MEMORY_LIMIT_EXCEEDED': 'MLE',
    }
    if verdict_text in verdict_dict:
        return verdict_dict[verdict_text]
    return 'WA'


def scrape_submissions_for_task(task_id, count=200):
    contest_id = task_id.split('_')[0]
    page_url = "http://codeforces.com/api/contest.status"

    id_from = 1
    found = True
    while found:
        found = False

        kwargs = {
            'contestId': contest_id,
            'from': id_from,
            'count': count,
        }
        response = get_page(page_url, **kwargs)
        json_data = json.loads(response.text)
        if json_data['status'] != 'OK':
            raise Exception('Expected status: OK; got: %s' % json_data['status'])

        for submission_data in json_data['result']:
            found = True

            submission_id = submission_data['id']
            check_task_id = '_'.join([
                str(submission_data['problem']['contestId']),
                submission_data['problem']['index']])

            if task_id != check_task_id:
                continue

            if submission_data['verdict'] == 'TESTING':
                print('Skipped submission %s: still testing.' % submission_id)
                continue

            if len(submission_data['author']['members']) != 1:
                print('Skipped submission %s: multiple authors not supported.' % submission_id)
                continue

            if 'verdict' not in submission_data:
                print('Skipped submission %s: no verdict?.' % submission_id)
                continue

            author_id = submission_data['author']['members'][0]['handle']
            submission = dict(
                submission_id=submission_id,
                task_id=task_id,
                submitted_on=datetime.datetime.utcfromtimestamp(submission_data['creationTimeSeconds']),
                language=submission_data['programmingLanguage'],
                verdict=__parse_verdict(submission_data['verdict']),
                author_id=author_id,
                time_exec=submission_data['timeConsumedMillis'],
                memory_used=round(submission_data['memoryConsumedBytes'] / 1024),
            )
            yield submission
        id_from += count


def scrape_submissions_for_tasks(task_ids):
    submissions = [scrape_submissions_for_task(task_id) for task_id in task_ids]
    return heapq.merge(*submissions, key=lambda x: x['submitted_on'], reverse=True)
