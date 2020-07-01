from scraper.utils import get_page
from bs4 import BeautifulSoup
from .parsers import parse_time_exec, parse_memory_used, parse_verdict, parse_date, parse_time_limit, parse_memory_limit

TIMUS_JUDGE_ID = 'timus'


def scrape_submissions(**query_args):
    url = "https://acm.timus.ru/status.aspx"
    response = get_page(
        url,
        space=query_args.pop('space', 1),
        count=query_args.pop('count', 1000),
        **query_args,
    )
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.select_one("table.status")

    for row in table.select("tr.odd, tr.even"):
        row = row.select('td')
        assert len(row) == 9
        submission = dict(
            judge_id=TIMUS_JUDGE_ID,
            submission_id=row[0].text,
            author_id=row[2].find("a", href=True)['href'].split('id=')[-1],
            task_id=str(int(row[3].text.split('.')[0])),
            submitted_on=parse_date(row[1].contents),
            verdict=parse_verdict(row[5].text),
            language=row[4].text
        )
        if row[7].text:
            submission['time_exec'] = parse_time_exec(row[7].text)
        if row[8].text:
            submission['memory_used'] = parse_memory_used(row[8].text)
        yield submission


def scrape_task_info(task_id, space=1):
    url = "https://acm.timus.ru/problem.aspx"
    response = get_page(
        url, num=task_id, space=space)
    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.select_one("h2.problem_title").text.split('.', 1)[1].strip()
    contents = soup.select_one("div.problem_limits").contents
    tl, ml = contents[0], contents[2]
    return {
        'judge_id': TIMUS_JUDGE_ID,
        'task_id': task_id,
        'title': title,
        'time_limit': parse_time_limit(tl),
        'memory_limit': parse_memory_limit(ml),
    }


