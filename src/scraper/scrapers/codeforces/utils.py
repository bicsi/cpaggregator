import datetime
import heapq
import re
from typing import Dict, Any

from bs4 import BeautifulSoup

from core import markdown 
from core.logging import log
from scraper.scrapers.codeforces.parsers import \
    parse_tag, parse_submission, CODEFORCES_JUDGE_ID, \
    parse_time_limit, parse_memory_limit, parse_filename
from scraper.utils import get_page, split_into_chunks


def _api_get(api_method: str, kwargs) -> Any:
    page_url = f"https://codeforces.com/api/{api_method}"
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


def scrape_recent_submissions(count=1000):
    response = _api_get('problemset.recentStatus', kwargs={
        'count': count,
    })
    for submission_data in response:
        for submission in parse_submission(submission_data):
            yield submission


def scrape_submissions_for_tasks(task_ids, count=200):
    submissions = [scrape_submissions_for_task(
        task_id, count=count) for task_id in task_ids]
    return heapq.merge(*submissions, key=lambda x: x['submitted_on'], reverse=True)


def scrape_submissions_for_task(task_id, count=1000):
    contest_id = task_id.split('/')[0]

    id_from = 1
    found = True
    while found:
        found = False

        response = _api_get('contest.status', kwargs={
            'contestId': contest_id,
            'from': id_from,
            'count': count,
        })

        for submission_data in response:
            found = True

            check_task_id = '/'.join([
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

        response = _api_get('user.status', kwargs={
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
    contest_id = task_id.split('/')[0]
    response = _api_get('contest.standings', kwargs={'contestId': contest_id})

    found = False
    for task_data in response['problems']:
        curr_task_id = '/'.join([str(task_data['contestId']),
                                 task_data['index']]).lower()
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
    response = _api_get('user.info', kwargs={'handles': ';'.join(handles)})
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
    contest_id, task_letter = task_id.split('/')
    contest_or_gym = "gym" if int(contest_id) >= 100000 else "contest"
    response = get_page(
        f"https://codeforces.com/{contest_or_gym}/{contest_id}/problem/{task_letter}")
    soup = BeautifulSoup(response.text, 'html.parser')
    statement = soup.select_one(".problem-statement")
    result = ""

    # print(statement.select_one('.time-limit'))
    # print(statement.select_one('.time-limit').string)

    task_info = {
        "time_limit": parse_time_limit(
            statement.select_one('.time-limit').find(text=True, recursive=False)),
        "memory_limit": parse_memory_limit(
            statement.select_one('.memory-limit').find(text=True, recursive=False)),
        "input_file": parse_filename(
            statement.select_one(".input-file").find(text=True, recursive=False)),
        "output_file": parse_filename(
            statement.select_one(".output-file").find(text=True, recursive=False)),
    }

    inputs = []
    outputs = []
    for child in statement.find_all("div", recursive=False):
        klass = child.get("class", [])
        if "header" in klass:
            continue
        if "sample-tests" in klass:
            for test in child.select('.sample-test'):
                for br in test.find_all('br'):
                    br.replace_with("\n" + br.text)
                for tag in test.select('.input pre'):
                    inputs.append(tag.text)
                for tag in test.select(".output pre"):
                    outputs.append(tag.text)
            continue
        result += str(child)

    result = f"<div>{result}</div>"
    soup = BeautifulSoup(result, 'html.parser')

    for node in soup.select(".section-title"):
        node.wrap(soup.new_tag("h3"))

    for node in soup.select(".tex-span"):

        inner_text = str(node)
        inner_text = inner_text.replace("&lt;", "<")
        inner_text = inner_text.replace("&gt;", ">")

        for c in "&%$#_{}":
            inner_text = inner_text.replace(c, '\\' + c)

        inner_text = re.sub(r"<span[^>]*>(.*)<\/span>", r"\g<1>", inner_text)
        inner_text = re.sub(r"<sub[^>]*>(.*?)<\/sub>", r"_{\g<1>}", inner_text)
        inner_text = re.sub(r"<sup[^>]*>(.*?)<\/sup>", r"^{\g<1>}", inner_text)
        inner_text = re.sub(r"<i[^>]*>(.*?)<\/i>", r"\g<1>", inner_text)

        code = soup.new_tag("latex")
        code.string = inner_text
        node.replace_with(code)

    for node in soup.select(".tex-font-style-tt"):
        code = soup.new_tag("latex")
        code.string = node.text
        node.replace_with(code)

    result = str(soup)
    latex_codes = []
    result = re.sub(r'\$\$\$(.*?)\$\$\$', '<latex>\g<1></latex>', result)
    
    # result = re.sub(r'\$\$\$(.*?)\$\$\$', "<code>$<1>$</code>", result)


    md = markdown.html2text(result)

    for match, repl in zip(reversed(list(re.finditer(r'`\[\[\[LATEX\]\]\]`', md))), latex_codes):
        [b, e] = match.span()
        md = md[:b] + '$' + repl + '$' + md[e:]

    examples = None
    if len(inputs) == len(outputs):
        examples = [{"input": i, "output": o} for i, o in zip(inputs, outputs)]
    else:
        log.critical(
            f"Could not parse examples for {task_id}: unequal number of inputs and outputs")

    print(md)

    task_info.update({
        "statement": md,
        "examples": examples,
    })
    return task_info


def crawl(output_path):
    queue = ['/']
    seen = {'/'}

    with open(output_path, 'w') as out:
        def process(url):
            log.info(f"Processing {url}")
            response = get_page(f"https://codeforces.com{url}", max_retries=1)
            soup = BeautifulSoup(response.content, "html.parser")
            for a in soup.find_all('a', href=True):
                href = a['href']
                href = href.split('codeforces.com')[-1].rstrip('/')
                if '#' in href or '?' in href or href.startswith('http'):
                    continue

                out.write(f"{url} {href}\n")
                if '/problem/' in href:
                    log.info(f"Found edge: {url}->{href}")

                if href in seen:
                    continue

                href = href.replace('profile', 'blog')

                if 'blog' in href:
                    seen.add(href)
                    queue.append(href)

        for it in range(10):
            now_queue = queue.copy()
            queue.clear()
            for url in now_queue:
                process(url)
