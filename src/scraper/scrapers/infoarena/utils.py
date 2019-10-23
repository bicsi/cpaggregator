from bs4 import BeautifulSoup

from core.logging import log
from scraper.utils import get_page
from scraper.scrapers.infoarena import parsers

SCRAPER_LIMIT = 1000 * 1000 * 1000
INFOARENA_JUDGE_ID = "ia"
USER_WITH_DEFAULT_AVATAR = 'florinas'


def __scrape_paginated_table_rows(page_url, from_page, to_page, results_per_page, table_css_selector, **query_dict):
    if results_per_page > 250:
        raise Exception("Infoarena does not support more than 250 results per page")

    for page_id in range(from_page, to_page + 1):
        first_entry = results_per_page * (page_id - 1)
        page = get_page(page_url, **query_dict,
                        first_entry=first_entry,
                        display_entries=results_per_page)
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.select_one(table_css_selector)
        if table is None:
            break
        if "Nici o solutie" in table.text:
            break

        rows = table.find_all("tr")[1:]
        for row in rows:
            yield row.find_all("td")


def scrape_submissions(from_page=1, to_page=SCRAPER_LIMIT, results_per_page=200, **query_dict):
    """
    Scrapes all submissions from the eval monitor.
    :param from_page: first page of the pagination
    :param to_page: last page of the pagination
    :param results_per_page: number of results to get for each request
    :param query_dict: optional GET query params to give to the monitor (e.g. user='retrograd')
    """
    page_url = "https://www.infoarena.ro/monitor"
    rows = __scrape_paginated_table_rows(page_url, from_page, to_page, results_per_page,
                                         table_css_selector="#monitor-table", **query_dict)
    for row in rows:
        if len(row) != 7:
            raise Exception("Unexpected number of columns.")
        # Parse required information.
        try:
            verdict_text = row[6].find("span").text
            submission = dict(
                judge_id=INFOARENA_JUDGE_ID,
                submission_id=row[0].find("a", href=True)['href'].split('/')[-1],
                author_id=row[1].find("a", href=True)['href'].split('/')[-1].lower(),
                task_id=row[2].find("a", href=True)['href'].split('/')[-1].lower(),
                source_size=parsers.parse_source_size(row[4].find("a").text),
                submitted_on=parsers.parse_date(row[5].text),
                verdict=parsers.parse_verdict(verdict_text),
                score=parsers.parse_score(verdict_text),
            )
            yield submission
        except (TypeError, AttributeError) as e:
            # Probably task name was hidden.
            log.warning(f"Skipped one submission. Error: {e}")


def scrape_task_ids(page_name, from_page=1, to_page=SCRAPER_LIMIT, results_per_page=200):
    """
    Scrapes task ids from a page.
    :param page_name: name of the page (e.g. "arhiva-educationala")
    :param from_page: first page of the pagination
    :param to_page: last page of the pagination
    :param results_per_page: number of results to get for each request
    :return: a generator of task ids
    """
    page_url = "https://www.infoarena.ro/" + page_name
    rows = __scrape_paginated_table_rows(page_url, from_page, to_page, results_per_page,
                                         table_css_selector=".tasks")
    for row in rows:
        task_id = row[1].find("a", href=True)['href'].split('/')[-1]
        yield task_id


def scrape_task_info(task_id):
    """
    Scrapes task information for a given task id.
    :param task_id: the id of the task
    :return: task information, in dict format
    """
    page_url = "https://www.infoarena.ro/problema/" + task_id
    page = get_page(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    main_view = soup.find(id='main')
    info_table = main_view.find('table')

    title = main_view.find('h1').text.strip()
    time_limit = info_table.find_all('tr')[2].find_all('td')[1].text
    memory_limit = info_table.find_all('tr')[2].find_all('td')[3].text
    source = info_table.find_all('tr')[0].find_all('td')[3].text

    tags = []
    for tag_a in main_view.select('a.tag_search_anchor'):
        tag = parsers.parse_tag(tag_a.text)
        if tag is not None:
            tags.append(tag)

    return {
        'judge_id': INFOARENA_JUDGE_ID,
        'task_id': task_id.lower(),
        'title': title,
        'source': source,
        'time_limit': parsers.parse_time_limit(time_limit),
        'memory_limit': parsers.parse_memory_limit(memory_limit),
        'tags': tags,
    }


def __get_avatar_url(handle):
    return "https://www.infoarena.ro/avatar/full/" + handle


def get_default_avatar():
    return get_page(__get_avatar_url(USER_WITH_DEFAULT_AVATAR)).content


def scrape_user_info(handle, default_avatar):
    """
    Scrapes user information for given handles.
    :param handle: the handle of infoarena user
    :param default_avatar: obtainable from get_default_avatar()
    :return: user information, in dict format
    """

    page_url = "https://www.infoarena.ro/utilizator/" + handle
    page = get_page(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    table = soup.select_one('table.compact')
    cells = list(table.select('td'))

    user_info = {
        'judge_id': INFOARENA_JUDGE_ID,
        'handle': handle.lower(),
        'rating': int(cells[3].text),
    }

    # FIXME: This may not be right!?
    full_name = cells[1].text
    if len(full_name.split()) == 1:
        user_info.update({
            'first_name': full_name,
            'last_name': None,
        })
    else:
        first_name, last_name = full_name.rsplit(' ', 1)
        user_info.update({
            'first_name': first_name,
            'last_name': last_name,
        })

    avatar_url = cells[0].find("a", href=True)['href']
    if avatar_url.lower() != f'/avatar/full/{handle.lower()}':
        raise Exception('Avatar url is not as expected.')

    user_avatar = get_page(__get_avatar_url(handle)).content
    if user_avatar == default_avatar:
        user_info['photo_url'] = None
    else:
        user_info['photo_url'] = __get_avatar_url(handle)
    return user_info