import re
from enum import Enum, auto
from types import SimpleNamespace
from typing import Optional, NamedTuple, Pattern

from django.urls import reverse

from core.logging import log


class ParseTaskResult(NamedTuple):
    judge_id: str
    task_id: str


class ParserType(Enum):
    SIMPLE = auto()
    COMPOSED = auto()


class Parser(NamedTuple):
    judge_id: str
    type: ParserType
    regex: Pattern[str]


TASK_PARSERS = [
    Parser(judge_id='cf', type=ParserType.COMPOSED,
           regex=re.compile(r'codeforces\.com/(gym|contest)/'
                            r'(?P<contest_id>\d+)/problem/(?P<task_id>[A-Za-z](\d)?)')),
    Parser(judge_id='ia', type=ParserType.SIMPLE,
           regex=re.compile(r'infoarena\.ro/problema/(?P<task_id>[^/]+)')),
    Parser(judge_id='ac', type=ParserType.COMPOSED,
           regex=re.compile(r'atcoder\.jp/contests/(?P<contest_id>[^/]+)/tasks/(?P<task_id>[^/]+)')),
    Parser(judge_id='csa', type=ParserType.SIMPLE,
           regex=re.compile(r'csacademy\.com/contest/(?P<contest_id>[^/]+)/task/(?P<task_id>[^/]+)')),
    Parser(judge_id='ojuz', type=ParserType.SIMPLE,
           regex=re.compile(r'oj\.uz/problem/(?P<action>[^/]+)/(?P<task_id>[^/]+)')),
    Parser(judge_id='cf', type=ParserType.COMPOSED,
           regex=re.compile(r'codeforces\.com/problemset/problem/(?P<contest_id>\d+)/(?P<task_id>[A-Za-z](\d)?)'))
]


def parse_task_url(url: str) -> Optional[ParseTaskResult]:
    result = re.search(r"https://competitive\.herokuapp\.com/"
                       r"task/(?P<judge_id>[^/]+)/(?P<task_id>[^/]+)", url)
    if result:
        return ParseTaskResult(judge_id=result.group("judge_id"),
                               task_id=result.group("task_id"))

    for parser in TASK_PARSERS:
        re_search = parser.regex.search(url)
        if not re_search:
            continue

        if parser.type == ParserType.SIMPLE:
            task_id = re_search.group('task_id')
        else:
            task_id = '/'.join([re_search.group('contest_id'),
                                re_search.group('task_id')])
        return ParseTaskResult(judge_id=parser.judge_id, task_id=task_id)

    log.warning(f'Could not parse URL: {url}.')
    return None

