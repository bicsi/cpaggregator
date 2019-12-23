import heapq

from bs4 import BeautifulSoup
import datetime
import re

from core.logging import log
from scraper.utils import get_page
from .parsers import parse_title, parse_time_limit, parse_memory_limit

PAGE_LIMIT = 1000 * 1000 * 1000
ATCODER_JUDGE_ID = "ac"


def __parse_contest_id(contest_url: str):
    result = re.search(r'https?://(.*)\.contest\.atcoder\.jp/?', contest_url)
    if result is None:
        log.warning(f"Could not parse contest id from {contest_url}.")
        return None
    return result.group(1)


def __get_contest_url(contest_id: str):
    return f'https://{contest_id}.contest.atcoder.jp/'


def __scrape_table_rows(node, table_css_selector):
    table = node.select_one(table_css_selector)
    if table is None:
        log.warning(f'Could not find table with selector {table_css_selector}')
        return

    for row in table.find("tbody").find_all("tr"):
        yield row.find_all("td")


def scrape_submissions_for_contest(contest_id, from_page=1, to_page=PAGE_LIMIT, **query_dict):
    """
    Scrapes all the submissions for a given contest.
    :param contest_id: the id of the contest (e.g. 'agc003')
    :param from_page: the page from which to start
    :param to_page: the page for which to end
    :param query_dict: query parameters for the url (e.g. user_screen_name='tourist')
    :return: a generator of submission objects
    """
    base_url = __get_contest_url(contest_id)

    for page_id in range(from_page, to_page + 1):
        page_url = f"{base_url}submissions/all/{page_id}"
        page = get_page(page_url, **query_dict)
        soup = BeautifulSoup(page.content, 'html.parser')
        rows = __scrape_table_rows(soup.select_one("#outer-inner"),
                                   table_css_selector="table")
        submission_found = False

        for row in rows:
            submission = {
                'judge_id': ATCODER_JUDGE_ID,
                'submission_id': row[-1].find('a', href=True)['href'].split('/')[-1],
                'submitted_on': datetime.datetime.strptime(
                    row[0].find('time').text, "%Y/%m/%d %H:%M:%S +0000"),
                'task_id': "/".join([contest_id, row[1].find('a', href=True)['href'].split('/')[-1]]).lower(),
                'author_id': row[2].find('a', href=True)['href'].split('/')[-1].lower(),
                'language': row[3].text,
                'source_size': int(row[5].text.split()[0]),
                'verdict': row[6].select_one('span.label.tooltip-label').text.split()[-1],
            }

            if row[4].text != '-':
                submission['score'] = int(row[4].text)

            if len(row) == 10:
                submission.update({
                    'exec_time': int(row[7].text.split()[0]),
                    'memory_used': int(row[8].text.split()[0]),
                })

            submission_found = True
            yield submission

        if not submission_found:
            break


def scrape_past_contest_ids():
    """
    Scrapes all past (finished) contests.
    :return: a list of contest ids (e.g. ['arc092', 'agc003'])
    """
    page_url = "https://atcoder.jp/contest/archive"

    contest_ids = set()
    for page_id in range(1, PAGE_LIMIT):
        page = get_page(page_url, p=page_id)
        soup = BeautifulSoup(page.content, 'html.parser')
        old_len = len(contest_ids)

        table = soup.find('table')
        for a in table.find_all('a', href=True):
            contest_url = a['href']
            contest_id = __parse_contest_id(contest_url)
            if contest_id is not None:
                contest_ids.add(contest_id)

        if old_len == len(contest_ids):
            break
    return list(contest_ids)


def scrape_submissions_for_user(user_id, contest_ids):
    """
    Scrapes all the submissions for a given user.
    Returns a generator of submissions (dict).
    :param user_id: the id of the user (e.g. 'tourist')
    :param contest_ids: the list of contests to consider (e.g. ['arc092', 'agc003'])
    :return: a generator of submission objects
    """
    for contest_id in contest_ids:
        submissions = scrape_submissions_for_contest(
            contest_id, user_screen_name=user_id)
        for submission in submissions:
            yield submission


def scrape_submissions_for_task(task_id):
    """
    Scrapes all submissions for a given task.
    :param task_id: the id of the task (e.g. 'agc003_a')
    :return: a generator of submission objects
    """
    contest_id, task_id = task_id.split('/')
    return scrape_submissions_for_contest(
        contest_id, task_screen_name=task_id)


def scrape_submissions_for_tasks(task_ids):
    submissions = [scrape_submissions_for_task(task_id) for task_id in task_ids]
    return heapq.merge(*submissions, key=lambda x: x['submitted_on'], reverse=True)


def scrape_task_info(task_id: str):
    """
    Scrapes the task info for given tasks.
    :param task_id: the id of the task (e.g. 'agc003/agc003_a')
    :return: a task info object
    """
    contest_id, task_id = task_id.split('/')
    page_url = f"https://atcoder.jp/contests/{contest_id}/tasks/{task_id}"
    page = get_page(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    main_div = soup.select_one('span.h2').parent
    time_limit_text, memory_limit_text = map(str.strip, main_div.select_one('p').text.split('/'))
    task_info = {
        'judge_id': ATCODER_JUDGE_ID,
        'task_id': "/".join([contest_id, task_id]).lower(),
        'title': parse_title(main_div.select_one('span.h2').text),
        'time_limit': parse_time_limit(time_limit_text),
        'memory_limit': parse_memory_limit(memory_limit_text),
        'tags': [],
        'source': soup.select_one('.contest-title').text,
    }
    return task_info
