import re
import datetime

MONTH_ENCODINGS = ['ian', 'feb', 'mar', 'apr', 'mai', 'iun', 'iul', 'aug', 'sep', 'oct', 'nov', 'dec']

TAG_DICT = {
    "Structuri de Date": "data_structures",
    "Geometrie": "geometry",
    "Matematica": "math",
    "Grafuri": "graphs",
    "Sortare": "sorting",
}


def parse_tag(tag_text):

    if tag_text in TAG_DICT:
        return TAG_DICT[tag_text]

    print("WARNING: Unknown tag: %s." % tag_text)
    return None


def parse_time_limit(time_limit_text: str):
    result = re.search(r'(\d+(\.\d+)?) sec', time_limit_text)
    if result is None:
        raise ValueError("Cannot parse time limit: %s" % time_limit_text)
    return int(1000 * float(result.group(1)))


def parse_memory_limit(memory_limit_text: str):
    result = re.search(r'(\d+) kbytes', memory_limit_text)
    if result is None:
        raise ValueError("Cannot parse memory limit: %s" % memory_limit_text)
    return int(result.group(1))


def parse_score(score_text: str):
    result = re.search(r'Evaluare completa: (\d+) puncte', score_text)
    if result is None:
        return None
    return int(result.group(1))


def parse_verdict(verdict_text: str):
    if ':' not in verdict_text:
        return None

    verdict, points = map(str.strip, verdict_text.split(':'))
    if verdict == 'Evaluare completa':
        if points == '100 puncte':
            return 'AC'
        return 'WA'
    if verdict == 'Eroare de compilare':
        return 'CE'
    return 'WA'


def parse_date(date_text: str):
    day, month, year, time = date_text.split()
    hour, minute, second = time.split(':')

    return datetime.datetime(
        year=2000 + int(year),
        month=MONTH_ENCODINGS.index(month) + 1,
        day=int(day),
        hour=int(hour),
        minute=int(minute),
        second=int(second),
        # TODO: Account for timezone difference.
    )


def parse_source_size(source_text: str):
    result = re.search(r'(\d+\.\d\d) kb', source_text)
    if result is None:
        raise ValueError("Could not parse source size: %s" % source_text)
    return int(float(result.group(1)) * 1000)