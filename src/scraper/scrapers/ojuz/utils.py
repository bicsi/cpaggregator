from bs4 import BeautifulSoup

from scraper.scrapers.ojuz import parsers
from scraper.utils import get_page

SCRAPER_LIMIT = 1000 * 1000 * 1000
OJUZ_JUDGE_ID = 'ojuz'


def __scrape_paginated_table_rows(page_url, from_page, to_page, table_css_selector, **query_dict):
    for page_id in range(from_page, to_page + 1):
        page = get_page(page_url, **query_dict,
                        page=page_id)
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.select_one(table_css_selector)

        rows = table.find_all("tr")[1:]
        if len(rows) == 0:
            break
        for row in rows:
            yield row.find_all("td")


def scrape_submissions(from_page=1, to_page=SCRAPER_LIMIT, **query_dict):
    """
    Scrapes all submissions from the eval monitor.
    :param from_page: first page of the pagination
    :param to_page: last page of the pagination
    :param query_dict: optional GET query params to give to the monitor
        (e.g. problem='BOI18_genetics', handle='retrograd')
    """
    page_url = "https://oj.uz/submissions"
    rows = __scrape_paginated_table_rows(page_url, from_page, to_page,
                                         table_css_selector=".container .table", **query_dict)
    for row in rows:
        if len(row) != 8:
            raise Exception("Unexpected number of columns.")
        # Parse required information.
        try:
            verdict_text = row[5].text
            submission = dict(
                judge_id=OJUZ_JUDGE_ID,
                submission_id=row[0].find("a", href=True)['href'].split('/')[-1],
                submitted_on=parsers.parse_date(row[1].text),
                author_id=row[2].find("a", href=True)['href'].split('/')[-1].lower(),
                task_id=row[3].find("a", href=True)['href'].split('/')[-1].lower(),
                verdict=parsers.parse_verdict(verdict_text),
                score=parsers.parse_score(verdict_text),
            )
            if submission['verdict'] != 'CE':
                submission.update(dict(
                    time_exec=parsers.parse_time_exec(row[6].text),
                    memory_used=parsers.parse_memory_used(row[7].text),
                ))
            yield submission
        except (TypeError, AttributeError) as e:
            # Probably task name was hidden.
            print(f"WARNING: Skipped one submission. ERROR: {e}")


def scrape_task_info(task_id):
    """
    Scrapes task information for a given task id.
    :param task_id: the id of the task
    :return: task information, in dict format
    """
    page_url = "https://oj.uz/problem/view/" + task_id
    page = get_page(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    title_div = soup.select_one('.problem-title')
    title = title_div.find('h1').text.lstrip().split('\n')[0].rstrip()
    cols = title_div.parent.select_one('.table-responsive').find_all('td')

    return {
        'judge_id': OJUZ_JUDGE_ID,
        'task_id': task_id.lower(),
        'title': title,
        'time_limit': parsers.parse_time_limit(cols[0].text),
        'memory_limit': parsers.parse_memory_limit(cols[1].text),
    }

print(scrape_task_info('boi18_genetics'))
