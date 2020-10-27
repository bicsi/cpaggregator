import re
import string

from bs4 import BeautifulSoup

from core import markdown
from core.logging import log
from scraper.utils import get_page
from scraper.scrapers.infoarena import parsers
from html2text import html2text
import unicodedata


def __strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


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
        submission_id = None
        try:
            verdict_text = row[6].find("span").text
            submission_id = row[0].find("a", href=True)['href'].split('/')[-1]
            if not row[4].find("a"):
                log.debug(f"Skipped submission #{submission_id}: private.")
                continue
            if verdict_text.startswith("Eroare"):
                log.debug(f"Skipped submission #{submission_id}: system error.")
                continue
            submission = dict(
                judge_id=INFOARENA_JUDGE_ID,
                submission_id=submission_id,
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
            log.warning(f"Error scraping submission #{submission_id}: {e}")


def get_submission_count(**query_dict):
    page_url = f"https://www.infoarena.ro/monitor"
    page = get_page(page_url, **query_dict)
    soup = BeautifulSoup(page.content, 'html.parser')
    submision_count_text = soup.select_one('#monitor-table .pager .count').text
    submission_count = parsers.parse_submission_count(submision_count_text)
    return submission_count


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
    input_file, output_file = map(str.strip, info_table.find_all('tr')[0].find_all('td')[1].text.split(','))
    time_limit = info_table.find_all('tr')[2].find_all('td')[1].text
    memory_limit = info_table.find_all('tr')[2].find_all('td')[3].text
    source = info_table.find_all('tr')[0].find_all('td')[3].text

    tags = []
    for tag_a in main_view.select('a.tag_search_anchor'):
        tag = parsers.parse_tag(tag_a.text)
        if tag is not None:
            tags.append(tag)

    task_info = {
        'judge_id': INFOARENA_JUDGE_ID,
        'task_id': task_id.lower(),
        'title': title,
        'source': source,
        'time_limit': parsers.parse_time_limit(time_limit),
        'memory_limit': parsers.parse_memory_limit(memory_limit),
        'input_file': input_file,
        'output_file': output_file,
        'tags': tags,
    }

    try:
        # Go to the monitor to find out submission count and first submission date.
        task_info.update(dict(
            total_submission_count=get_submission_count(task=task_id),
            accepted_submission_count=get_submission_count(task=task_id, score_begin=100)))

        submission_count = task_info['total_submission_count']
        if submission_count > 0:
            # A little hack to get only the very first submissions.
            first_few_submissions = list(scrape_submissions(
                from_page=max(1, submission_count // 20 - 1),
                results_per_page=20,
                task=task_id))
            if len(first_few_submissions) == 0:
                raise Exception("BUG: First few submissions are non-existant")

            first_submitted_on = min([sub['submitted_on'] for sub in first_few_submissions])
            task_info['first_submitted_on'] = first_submitted_on
    except Exception as ex:
        log.warning(f"Failed to parse extra data for task {task_id}: {ex}")

    return task_info


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


def scrape_task_statement(task_id: str):
    response = get_page(f"https://www.infoarena.ro/problema/{task_id}")
    soup = BeautifulSoup(response.text, 'html.parser')
    text_block = soup.select_one("#main > .wiki_text_block")

    found_h1 = False
    text_lines = []
    html = ""
    for child in text_block.find_all(recursive=False):
        if child.name == 'h1':
            found_h1 = True
            continue
        if not found_h1:
            continue
        if "Exempl" in child.text:
            break
        text_lines.append(child.text)
        html += str(child)

    html = html\
        .replace('`', '\'')\
        .replace('<var>', '<code>')\
        .replace('</var>', '</code>')\
        .replace('<h2>', '<h3>')\
        .replace('</h2>', '</h3>')

    def remove_text(match):
        if len(match.split()) <= 6:
            return None

        ret = []
        found_words = 0
        word_streak = 0
        for token in match.split():
            is_word = False
            stripped = __strip_accents(token)
            for c in string.punctuation:
                stripped = stripped.rstrip(c)
            stripped = "".join([c for c in stripped if c != '-'])

            if (len(stripped) > 1 and stripped.isalpha()) or \
                    (stripped.lower() in ['o', 'a', 'e'] and word_streak >= 2):
                is_word = True
                found_words += len(stripped)
            if not is_word:
                ret.append(f"<code>{token}</code>")
                word_streak = 0
            else:
                ret.append(token)
                word_streak += 1

        if found_words <= 12:
            return None
        return " ".join(ret)

    for match in set(re.findall(r'<code>(.*?)<\/code>', html)):
        if '.in' in match or '.out' in match:
            if '<' in match:
                repl = re.sub(r"<[^>]*>", "", match)
                html = html.replace(match, repl)
            continue
        replace = remove_text(match)
        if replace:
            html = html.replace(f"<code>{match}</code>", f"{replace}")

    for match in set(re.findall(r'<code>(.*?)<\/code>', html)):
        if '.in' in match or '.out' in match:
            continue

        for c in ['\'', '\"']:
            if match.startswith(c) and match.endswith(c):
                continue

        latex = match
        latex = latex.replace('&lt;', '<').replace('&gt;', '>')

        for c in "&%$#_{}":
            latex = latex.replace(c, '\\' + c)

        latex = latex.replace('\\\'', '\'') \
            .replace('<sub>', '_{') \
            .replace('</sub>', '}') \
            .replace('<sup>', '^{') \
            .replace('</sup>', '}') \
            .replace('<b>', '\\textbf{') \
            .replace('</b>', '}') \
            .replace(' * ', ' \\cdot ') \
            .replace('<i>', '\\textit{') \
            .replace('</i>', '}')
        latex = re.sub('<[^>]+>', '', latex)

        sub = {}
        for idx, occ in enumerate(set(re.findall(r"\{([^\}]*)\}", latex))):
            nidx = f"__{idx}__"
            latex = latex.replace("{" + occ + "}", "{" + nidx + "}")
            sub[nidx] = occ

        latex = re.sub(r'([^a-zA-Z\\]|^)([a-zA-Z][a-zA-Z]*[a-zA-Z])', r"\g<1>\\text{\g<2>}", latex)

        latex = re.sub(r"\s+", ' ', latex)
        latex = latex.replace(" ", "$</code> <code>$")
        for nidx, occ in sub.items():
            latex = latex.replace("{" + nidx + "}", "{" + occ + "}")

        html = html.replace(f"<code>{match}</code>", f"<code>${latex}$</code>")

    html = re.sub(r"([(\[])<code>\$([^<]+)\$</code>([)\]])", r"<code>$\g<1>\g<2>\g<3>$</code>", html)

    examples = []
    for table in soup.select("table.example"):
        for tr in table.select("tr"):
            tds = list(tr.select("td"))
            if len(tds) == 0:
                continue

            if len(tds) == 1:
                log.critical(f"Failed parsing example for task: {task_id} -- odd number of tds")
                continue

            examples.append({
                "input": tds[0].text,
                "output": tds[1].text,
            })

    soup = BeautifulSoup(html, 'html.parser')
    for img in soup.find_all('img'):
        if 'latex' in img['src']:
            latex_formula = img['alt']
            latex_tag = soup.new_tag('code')
            latex_tag.string = "$" + latex_formula + "$"
            img.replace_with(latex_tag)
    html = str(soup)

    md = html2text(html, bodywidth=0)

    md = re.sub(r'\$`\s*`\$', ' ', md)
    md = re.sub(r'`\$(.*?)\$`', '%%%\g<1>%%%', md)
    md = re.sub(r'(?<!`)\$', '\\$', md)
    md = md.replace('%%%', '$')
    md = markdown.prettify(md)
    print(md)

    return {
        "statement": md,
        "examples": examples,
    }

