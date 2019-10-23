import datetime
import heapq

import requests
import json

from core.logging import log

CSACADEMY_JUDGE_ID = 'csa'


def __get_headers(csrf_token):
    return {
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        'Accept': '*/*',
        'Cache-Control': 'no-cache',
        'x-requested-with': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'https://csacademy.com/contest/archive/task/addition/submissions/',
        'x-csrftoken': csrf_token,
    }


def __get_cookies(csrf_token):
    return {
        'G_AUTHUSER_H': '0',
        'csrftoken': csrf_token,
        'G_ENABLED_IDPS': 'google',
    }


def get_task_info(csrf_token):
    response = requests.get('https://csacademy.com/contest/archive/task/addition/submissions/',
                            headers=__get_headers(csrf_token), cookies=__get_cookies(csrf_token))
    json_data = json.loads(response.text)

    return json_data['state']['contesttask']


def get_task_name_dict(csrf_token):
    task_name_to_id = {}
    for task in get_task_info(csrf_token):
        task_name_to_id.update({task['name']: task})
    return task_name_to_id


def get_eval_jobs(csrf_token, contest_task_id, from_date, num_jobs=1000):
    from_timestamp = from_date.timestamp()
    params = (
        ('numJobs', num_jobs),
        ('requestCount', 'false'),
        ('contestId', '1'),
        ('contestTaskId', contest_task_id),
        ('endTime', from_timestamp),
    )

    response = requests.get('https://csacademy.com/eval/get_eval_jobs/',
                            headers=__get_headers(csrf_token),
                            params=params, cookies=__get_cookies(csrf_token))
    json_data = json.loads(response.text)
    log.info(len(json_data['state']['evaljob']))
    return json_data['state']


def get_csrf_token():
    response = requests.get('https://csacademy.com/')
    csrf_token = response.cookies['csrftoken']
    log.debug('Got csrf token: {}'.format(csrf_token))
    return csrf_token


def parse_submissions(csrf_token, task_name, task_id, from_date):
    eval_jobs = get_eval_jobs(csrf_token, task_id, from_date)
    if 'publicuser' not in eval_jobs:
        log.error("'publicuser' not in eval_jobs", eval_jobs, task_name)
        return

    # Make user id to username map. We use usernames. :)
    user_id_to_username = {}
    for user in eval_jobs['publicuser']:
        username = user['username']
        user_id = user['id']
        if username:
            username = username.lower()
        user_id_to_username[user_id] = username

    # Parse submissions.
    for eval_job in reversed(eval_jobs['evaljob']):
        submission_id = eval_job['id']
        if not eval_job['isDone']:
            log.info(f'Skipping submission {submission_id}: Not finished evaluating.')

        # Parse easy data.
        submission = dict(
            judge_id=CSACADEMY_JUDGE_ID,
            submission_id=submission_id,
            submitted_on=datetime.datetime.utcfromtimestamp(eval_job['timeSubmitted']),
            task_id=task_name.lower(),
            author_id=user_id_to_username[eval_job['userId']],
            source_size=len(eval_job['sourceText']),
            verdict='CE',
        )

        # Parse verdict.
        verdict = 'CE'
        score = None
        if eval_job['compileOK']:
            score = round(eval_job['score'] * 100)
            if score == 100:
                verdict = 'AC'
            else:
                verdict = 'WA'

        if verdict != 'CE':
            submission.update(dict(
                verdict=verdict,
                score=score,
            ))

        # Parse memory_used and time_exec.
        time_exec = 0
        memory_used = 0

        for test in eval_job['tests']:
            time_exec = max(time_exec, test['wallTime'])
            memory_used = max(memory_used, test['memUsage'])

        time_exec = round(time_exec * 1000)
        memory_used = round(memory_used / 1024)

        submission.update(dict(
            time_exec=time_exec,
            memory_used=memory_used,
        ))

        # If author has no username, put the user id (Facebook-created accounts?).
        if submission['author_id'] is None:
            submission['author_id'] = 'uid:%s' % eval_job['userId']
        yield submission


def scrape_submissions_for_task(csrf_token, task_name, task_id):
    from_date = datetime.datetime.now() + datetime.timedelta(days=2)

    found = True
    while found:
        found = False

        submissions = parse_submissions(
            csrf_token, task_name,
            task_id,
            from_date=from_date
        )
        for submission in submissions:
            found = True
            from_date = submission['submitted_on']
            yield submission

        from_date = from_date - datetime.timedelta(microseconds=1)


def scrape_submissions_for_tasks(tasks):
    csrf_token = get_csrf_token()
    task_name_dict = get_task_name_dict(csrf_token)

    submissions = []
    for task_name in tasks:
        if task_name in task_name_dict:
            submissions.append(scrape_submissions_for_task(
                csrf_token, task_name, task_name_dict[task_name]['id']))
        else:
            log.error(f"Task '{task_name}' not found.")

    return heapq.merge(*submissions, key=lambda x: x['submitted_on'], reverse=True)


def scrape_all_task_info(csrf_token):
    response = requests.post('https://csacademy.com/contest/archive/?',
                             headers=__get_headers(csrf_token),
                             cookies=__get_cookies(csrf_token))
    json_data = json.loads(response.text)

    for task_data in json_data['state']['contesttask']:
        task_name = task_data['name']
        yield {
            'judge_id': CSACADEMY_JUDGE_ID,
            'task_id': task_name.lower(),
            'title': task_data['longName'],
            'tags': [],
        }
