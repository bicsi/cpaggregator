import datetime
import heapq

from core.logging import log
from scraper.scrapers.codeforces.parsers import parse_tag, parse_verdict
from scraper.utils import get_page, split_into_chunks
import json

CODEFORCES_JUDGE_ID = 'cf'


def scrape_submissions_for_tasks(task_ids, count=200):
    submissions = [scrape_submissions_for_task(task_id, count=count) for task_id in task_ids]
    return heapq.merge(*submissions, key=lambda x: x['submitted_on'], reverse=True)


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
        try:
            response = get_page(page_url, **kwargs)
        except Exception as e:
            log.exception(e)
            return []

        json_data = json.loads(response.text)
        if json_data['status'] != 'OK':
            raise Exception('Expected status: OK; got: %s' % json_data['status'])

        for submission_data in json_data['result']:
            found = True

            submission_id = submission_data['id']
            check_task_id = '_'.join([
                str(submission_data['problem']['contestId']),
                submission_data['problem']['index']])

            if task_id.lower() != check_task_id.lower():
                continue

            if submission_data['verdict'] == 'TESTING':
                log.info(f'Skipped submission {submission_id}: still testing.')
                continue

            if 'verdict' not in submission_data:
                log.warning(f'Skipped submission {submission_id}: no verdict?.')
                continue

            for author in submission_data['author']['members']:
                author_id = author['handle']
                submission = dict(
                    judge_id=CODEFORCES_JUDGE_ID,
                    submission_id=str(submission_id),
                    task_id=task_id.lower(),
                    submitted_on=datetime.datetime.utcfromtimestamp(submission_data['creationTimeSeconds']),
                    language=submission_data['programmingLanguage'],
                    verdict=parse_verdict(submission_data['verdict']),
                    author_id=author_id.lower(),
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
    for task_id in task_ids:
        try:
            page_url = "http://codeforces.com/api/contest.standings"
            contest_id = task_id.split('_')[0]
            response = get_page(page_url, contestId=contest_id)
            json_data = json.loads(response.text)
            if json_data['status'] != 'OK':
                raise Exception('Expected status: OK; got: %s' % json_data['status'])

            found = False
            for task_data in json_data['result']['problems']:
                curr_task_id = '_'.join([str(task_data['contestId']), task_data['index']]).lower()
                if task_id != curr_task_id:
                    continue

                log.info(f"Updating task '{task_id}' [{task_data['name']}]...")

                tags = []
                for tag_data in task_data['tags']:
                    tag = parse_tag(tag_data)
                    if tag:
                        tags.append(tag)
                task_info = {
                    'judge_id': CODEFORCES_JUDGE_ID,
                    'task_id': task_id.lower(),
                    'title': task_data['name'],
                    'tags': tags,
                    'source': json_data['result']['contest']['name'],
                }
                found = True
                yield task_info

            if not found:
                raise Exception(f"Task id '{task_id}' not found.")
        except Exception as e:
            log.exception(f'{e}')


def scrape_user_info(handles):
    """
    Scrapes user information from the website.
    :param handles: a list of codeforces handles
    """
    page_url = "http://codeforces.com/api/user.info"
    for handle_chunk in split_into_chunks(handles, chunk_size=1):
        try:
            response = get_page(page_url, handles=';'.join(handle_chunk))
            json_data = json.loads(response.text)
            if json_data['status'] != 'OK':
                raise Exception('Expected status: OK; got: %s' % json_data['status'])

            for user_data in json_data['result']:
                info = {
                    'judge_id': CODEFORCES_JUDGE_ID,
                    'handle': user_data['handle'].lower(),
                }
                if 'titlePhoto' in user_data and not user_data['titlePhoto'].endswith('no-title.jpg'):
                    info['photo_url'] = 'https:' + user_data['titlePhoto']
                if 'firstName' in user_data:
                    info['first_name'] = user_data['firstName']
                if 'lastName' in user_data:
                    info['last_name'] = user_data['lastName']

                yield info
        except Exception as e:
            log.exception(f'Exception trying to fetch chunk: {e}')
