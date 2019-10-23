import datetime
import heapq
from typing import Dict, Any

from core.logging import log
from scraper.scrapers.codeforces.parsers import parse_tag, parse_verdict
from scraper.utils import get_page, split_into_chunks

CODEFORCES_JUDGE_ID = 'cf'


def _get_(api_method: str, kwargs) -> Any:
    page_url = f"http://codeforces.com/api/{api_method}"
    try:
        response = get_page(page_url, **kwargs)
    except Exception as e:
        log.exception(e)
        return []

    json_data = response.json()
    status = json_data['status']
    if status != 'OK':
        raise Exception(f"Codeforces API error", "expected status: 'OK' got: '{status}'", api_method, kwargs)
    return json_data['result']


def scrape_submissions_for_tasks(task_ids, count=200):
    submissions = [scrape_submissions_for_task(task_id, count=count) for task_id in task_ids]
    return heapq.merge(*submissions, key=lambda x: x['submitted_on'], reverse=True)


def scrape_submissions_for_task(task_id, count=200):
    contest_id = task_id.split('_')[0]

    id_from = 1
    found = True
    while found:
        found = False

        response = _get_('contest.status', kwargs={
            'contestId': contest_id,
            'from': id_from,
            'count': count,
        })

        for submission_data in response:
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


def scrape_task_info(task_id: str):
    """
    Scrapes task information for given task ids.
    :param task_id: the id of the task
    :return: task information, in dict format
    """
    contest_id = task_id.split('_')[0]
    response = _get_('contest.standings', kwargs={'contestId': contest_id})

    found = False
    for task_data in response['problems']:
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
            'source': response['contest']['name'],
        }
        found = True
        yield task_info

    if not found:
        raise Exception(f"Task id '{task_id}' not found.")


def scrape_user_info(handles):
    """
    Scrapes user information from the website.
    :param handles: a list of codeforces handles
    """
    response = _get_('user.info', kwargs={'handles': ';'.join(handles)})
    user_infos = []
    for user_data in response:
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

        user_infos.append(info)
    return user_infos
