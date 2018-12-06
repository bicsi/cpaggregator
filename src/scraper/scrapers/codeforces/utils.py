import datetime
import heapq

from scraper.scrapers.codeforces.parsers import parse_tag
from scraper.utils import get_page
import json

CODEFORCES_JUDGE_ID = 'cf'




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
                judge_id=CODEFORCES_JUDGE_ID,
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


def scrape_task_info(task_ids):
    """
    Scrapes task information for given task ids.
    :param task_ids: the id of the tasks
    :return: task information, in dict format
    """
    page_url = "http://codeforces.com/api/problemset.problems"
    response = get_page(page_url)
    json_data = json.loads(response.text)
    if json_data['status'] != 'OK':
        raise Exception('Expected status: OK; got: %s' % json_data['status'])

    for task_data in json_data['result']['problems']:
        tags = []
        for tag_data in task_data['tags']:
            tag = parse_tag(tag_data)
            if tag:
                tags.append(tag)

        task_id = '_'.join([str(task_data['contestId']), task_data['index']])
        if task_id not in task_ids:
            continue

        yield {
            'judge_id': CODEFORCES_JUDGE_ID,
            'task_id': task_id,
            'title': task_data['name'],
            'tags': tags,
        }
