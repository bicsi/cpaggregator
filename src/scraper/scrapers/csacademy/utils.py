import datetime
import heapq

import requests
import json

CSACADEMY_JUDGE_ID = 'csa'


def __get_headers(csrftoken):
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
        'x-csrftoken': csrftoken,
    }


def __get_cookies(csrftoken):
    return {
        'G_AUTHUSER_H': '0',
        'csrftoken': csrftoken,
        'G_ENABLED_IDPS': 'google',
    }


def get_task_info(csrftoken):
    response = requests.get('https://csacademy.com/contest/archive/task/addition/submissions/',
                            headers=__get_headers(csrftoken), cookies=__get_cookies(csrftoken))
    json_data = json.loads(response.text)

    return json_data['state']['contesttask']


def get_task_name_dict(csrftoken):
    task_name_to_id = {}
    for task in get_task_info(csrftoken):
        task_name_to_id.update({task['name']: task})
    return task_name_to_id


def get_eval_jobs(csrftoken, contest_task_id, from_date, num_jobs=1000):
    from_timestamp = from_date.timestamp()

    params = (
        ('numJobs', num_jobs),
        ('requestCount', 'false'),
        ('contestId', '1'),
        ('contestTaskId', contest_task_id),
        ('endTime', from_timestamp),
    )

    response = requests.get('https://csacademy.com/eval/get_eval_jobs/',
                            headers=__get_headers(csrftoken),
                            params=params, cookies=__get_cookies(csrftoken))
    json_data = json.loads(response.text)
    return json_data['state']


def get_csrftoken():
    response = requests.get('https://csacademy.com/')
    csrftoken = response.cookies['csrftoken']
    print('Got csrftoken: {}'.format(csrftoken))
    return csrftoken


def parse_submissions(csrftoken, task_name, task_id, from_date):
    eval_jobs = get_eval_jobs(csrftoken, task_id, from_date)
    if 'publicuser' not in eval_jobs:
        return

    # Make user id to username map. We use usernames. :)
    user_id_to_username = {}
    for user in eval_jobs['publicuser']:
        user_id_to_username.update({user['id']: user['username']})

    # Parse submissions.
    for eval_job in reversed(eval_jobs['evaljob']):
        submission_id = eval_job['id']
        if not eval_job['isDone']:
            print('Skipping submission %s: Not finished evaluating.' % submission_id)

        # Parse easy data.
        submission = dict(
            judge_id=CSACADEMY_JUDGE_ID,
            submission_id=submission_id,
            submitted_on=datetime.datetime.utcfromtimestamp(eval_job['timeSubmitted']),
            task_id=task_name.lower(),
            author_id=user_id_to_username[eval_job['userId']].lower(),
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


def scrape_submissions_for_task(csrftoken, task_name, task_id):
    from_date = datetime.datetime.now() + datetime.timedelta(days=2)

    print(task_name)
    found = True
    while found:
        found = False

        print("From date: %s" % from_date)
        submissions = parse_submissions(
            csrftoken, task_name,
            task_id,
            from_date=from_date
        )
        for submission in submissions:
            found = True
            from_date = submission['submitted_on']
            yield submission

        from_date = from_date - datetime.timedelta(microseconds=1)


def scrape_submissions_for_tasks(tasks):
    csrftoken = get_csrftoken()
    task_name_dict = get_task_name_dict(csrftoken)

    submissions = [scrape_submissions_for_task(
        csrftoken, task_name, task_name_dict[task_name]['id'])
            for task_name in tasks]

    return heapq.merge(*submissions, key=lambda x: x['submitted_on'], reverse=True)


def scrape_task_info(tasks):
    csrftoken = get_csrftoken()
    response = requests.post('https://csacademy.com/contest/archive/?',
                             headers=__get_headers(csrftoken),
                             cookies=__get_cookies(csrftoken))
    json_data = json.loads(response.text)

    for task_data in json_data['state']['contesttask']:
        task_name = task_data['name']
        if task_name in tasks:
            yield {
                'judge_id': CSACADEMY_JUDGE_ID,
                'task_id': task_name.lower(),
                'title': task_data['longName'],
                'tags': [],
            }
