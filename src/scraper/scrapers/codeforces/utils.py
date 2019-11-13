import datetime
import heapq
from typing import Dict, Any

from bs4 import BeautifulSoup

from core.logging import log
from scraper.scrapers.codeforces.parsers import parse_tag, parse_submission, CODEFORCES_JUDGE_ID
from scraper.utils import get_page, split_into_chunks


def _get_(api_method: str, kwargs) -> Any:
    page_url = f"http://codeforces.com/api/{api_method}"
    try:
        response = get_page(page_url, **kwargs)
    except Exception as ex:
        log.error(f"GET request got exception: {ex}")
        return []

    json_data = response.json()
    status = json_data['status']
    if status != 'OK':
        log.error(f"Codeforces API error "
                  f"(expected status: 'OK' got: '{status}', "
                  f"message: '{json_data.get('comment')}')")
        return []
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

            check_task_id = '_'.join([
                str(submission_data['problem']['contestId']),
                submission_data['problem']['index']])

            if task_id.lower() != check_task_id.lower():
                continue

            for submission in parse_submission(submission_data):
                yield submission
        id_from += count


def scrape_submissions_for_user(handle, count=200):
    id_from = 1
    found = True
    while found:
        found = False

        response = _get_('user.status', kwargs={
            'handle': handle,
            'from': id_from,
            'count': count,
        })

        for submission_data in response:
            found = True

            for submission in parse_submission(submission_data):
                if submission['author_id'] == handle.lower():
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
        creation_time_seconds = response['contest'].get('startTimeSeconds')
        if creation_time_seconds:
            task_info['first_submitted_on'] = datetime.datetime.utcfromtimestamp(
                creation_time_seconds)
        found = True
        return task_info

    if not found:
        log.warning(f"Task id '{task_id}' not found.")
        return None


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


def scrape_task_statement(task_id: str):
    contest_id, task_letter = task_id.split('_')
    contest_or_gym = "gym" if int(contest_id) >= 100000 else "contest"
    response = get_page(f"https://codeforces.com/{contest_or_gym}/{contest_id}/problem/{task_letter}")
    soup = BeautifulSoup(response.text)
    statement = soup.select_one(".problem-statement")
    section_text = []
    for child in statement.findChildren("div", recursive=False):
        klass = child.get("class", [])
        if "header" in klass or "sample-tests" in klass:
            continue
        section_text.append(child.get_text(separator=" "))
    return "\n".join(section_text)
