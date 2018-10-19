import datetime
import time

from dateutil import parser
from selenium import webdriver

from scraper.utils import get_page

CSACADEMY_JUDGE_ID = "csa"


def __try_until(func, exception, max_tries=10, sleep_time=1):
    for _ in range(0, max_tries):
        try:
            return func()
        except exception as e:
            print('Error: %s\nRetrying...' % e)
            time.sleep(sleep_time)
    raise RuntimeError('__try_until failed after %s tries' % max_tries)


def __parse_score(verdict_text: str):
    if 'points' in verdict_text:
        points = float(verdict_text.split()[0])
        return int(points)
    return None


def __parse_verdict(verdict_text: str):
    points = __parse_score(verdict_text)
    if points is not None:
        if points == 100:
            return 'AC'
        return 'WA'
    if verdict_text == 'Compilation Error':
        return 'CE'
    raise Exception('Could not parse verdict text: %s' % verdict_text)


def __parse_memory_used(memory_used_text: str):
    value, unit = memory_used_text.split()
    unit_dict = {
        'B': 1 / 1024,
        'KB': 1,
        'MB': 1024,
    }
    return int(float(value) * unit_dict[unit])


def __parse_source_size(source_size_text: str):
    value, unit = source_size_text.split()
    unit_dict = {
        'B': 1,
        'KB': 1024,
    }
    return int(float(value) * unit_dict[unit])


def __parse_exec_time(exec_time_text: str):
    value, unit = exec_time_text.split()
    unit_dict = {
        'ms': 1,
    }
    return int(float(value) * unit_dict[unit])


def scrape_submissions_for_task(task_id, from_date=None):
    page_url = 'https://csacademy.com/contest/archive/task/%s/submissions/' % task_id
    get_page(page_url)

    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    with webdriver.Chrome(chrome_options=options) as driver:
        driver.implicitly_wait(20)
        driver.get(page_url)

        last_date: datetime.datetime = from_date
        while True:
            if last_date is not None:
                # Expand the filter.
                filter_jobs_expander = driver.find_element_by_xpath('.//div[contains(text(), "Filter jobs")]')
                __try_until(filter_jobs_expander.click, Exception)

                date_input = driver.find_element_by_xpath('.//*[contains(text(), "Before")]') \
                    .find_element_by_xpath('../..') \
                    .find_element_by_tag_name('input')
                next_date = datetime.datetime.strftime(
                    last_date - datetime.timedelta(seconds=1),
                    "%d/%m/%Y %H:%M:%S"
                )
                print('Setting filter to: %s' % next_date)
                __try_until(date_input.clear, Exception)
                __try_until(lambda: date_input.send_keys(next_date), Exception)
                __try_until(driver.find_element_by_xpath('.//button[contains(text(), "Set filter")]').click, Exception)
                __try_until(filter_jobs_expander.click, Exception)

            last_date = None

            for submission_box in driver.find_elements_by_xpath('.//div[contains(@class, "submissionSummary")]'):
                try:
                    submission = {
                        'judge_id': CSACADEMY_JUDGE_ID,
                        'task_id': task_id,
                    }

                    # Populate job id.
                    href = submission_box.find_element_by_xpath('.//a[contains(@href, "submission")]').get_attribute('href')
                    submission['submission_id'] = href.split('/')[-1]

                    # Populate date.
                    date_text = ' '.join(submission_box.text.split()[2:6])
                    submission['submitted_on'] = parser.parse(date_text)
                    last_date = submission['submitted_on']

                    # Click on submission and go to summary.
                    __try_until(submission_box.click, Exception)
                    summary_a = driver.find_element_by_xpath('.//a[contains(text(), "Summary")]')
                    __try_until(summary_a.click, Exception)
                    user_p = driver.find_element_by_xpath('.//p[contains(text(), "User")]')

                    verdict_text = user_p.find_element_by_xpath('../../div').text

                    # Populate author. Real author.
                    __try_until(user_p
                                .find_element_by_tag_name('b')
                                .find_element_by_xpath('..')
                                .click, Exception)
                    href = driver.find_element_by_xpath('.//a[contains(@href, "user")]').get_attribute('href')
                    if 'userid' in href:
                        print('Skipped submission of user: %s' % href)
                        driver.find_element_by_css_selector('button.close').click()
                        continue
                    submission['author_id'] = href.split('/')[-1]

                    for line in verdict_text.split('\n'):
                        k, v = map(str.strip, line.split(':'))
                        if k == 'Verdict':
                            submission['verdict'] = __parse_verdict(v)
                            score = __parse_score(v)
                            if score is not None:
                                submission['score'] = score
                        if k == 'Language':
                            submission['language'] = v
                        if k == 'CPU Time usage':
                            submission['exec_time'] = __parse_exec_time(v)
                        if k == 'Memory usage':
                            submission['memory_used'] = __parse_memory_used(v)
                        if k == 'Source code':
                            submission['source_size'] = __parse_source_size(v)

                    driver.find_element_by_css_selector('button.close').click()
                    print('Submission %s parsed successfully.' % submission['submission_id'])
                    yield submission
                except Exception as e:
                    print("Could not parse submission")
                    print("Error: %s" % e)
                    break

            if last_date is None:
                break
