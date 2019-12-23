import datetime

from core.logging import log

CODEFORCES_JUDGE_ID = 'cf'

TAG_DICT = {
    'graphs': 'graphs',
    'graph matchings': 'graphs',
    'shortest paths': 'graphs',
    'dfs and similar': 'graphs',
    '2-sat': 'graphs',
    'bitmasks': 'bitmask',
    'constructive algorithms': 'constructive',
    'greedy': 'greedy',
    'brute force': 'brute',
    'chinese remainder theorem': 'number-theory',
    'number theory': 'number-theory',
    'math': 'math',
    'matrices': 'math',
    'probabilities': 'math',
    'games': 'math',
    'trees': 'trees',
    'data structures': 'data-structures',
    'dsu': 'data-structures',
    'implementation': 'implementation',
    'expression parsing': 'implementation',
    'strings': 'strings',
    'string suffix structures': 'strings',
    'geometry': 'geometry',
    'binary search': 'search',
    'ternary search': 'search',
    'dp': 'dp',
    'flows': 'flow',
    'sortings': 'sorting',
    'combinatorics': 'combinatorics',
    'divide and conquer': 'divide',
}

VERDICT_DICT = {
    'OK': 'AC',
    'COMPILATION_ERROR': 'CE',
    'RUNTIME_ERROR': 'RE',
    'TIME_LIMIT_EXCEEDED': 'TLE',
    'MEMORY_LIMIT_EXCEEDED': 'MLE',
    'WRONG_ANSWER': 'WA',
}


def parse_tag(tag_text):
    if tag_text in TAG_DICT:
        return TAG_DICT[tag_text]

    log.warning(f"Unknown tag: {tag_text}.")
    return None


def parse_verdict(verdict_text):
    if verdict_text in VERDICT_DICT:
        return VERDICT_DICT[verdict_text]

    log.warning(f'Unknown verdict: {verdict_text}.')
    return 'WA'


def parse_submission(submission_data):
    try:
        submission_id = submission_data['id']
        task_id = '/'.join([
            str(submission_data['problem']['contestId']),
            submission_data['problem']['index']])

        if submission_data['verdict'] == 'TESTING':
            log.info(f'Skipped submission {submission_id}: still testing.')
            return []

        if 'verdict' not in submission_data:
            log.warning(f'Skipped submission {submission_id}: no verdict?.')
            return []

        for author in submission_data['author']['members']:
            author_id = author['handle']
            submission = dict(
                judge_id=CODEFORCES_JUDGE_ID,
                submission_id=str(submission_id),
                task_id=task_id.lower(),
                submitted_on=datetime.datetime.utcfromtimestamp(submission_data['creationTimeSeconds']),
                language=submission_data['programmingLanguage'],
                verdict=parse_verdict(submission_data['verdict']),
                author_id=author_id.lower(),
                time_exec=submission_data['timeConsumedMillis'],
                memory_used=round(submission_data['memoryConsumedBytes'] / 1024),
            )
            yield submission
    except Exception as ex:
        log.error(f"Failed to parse submission.\nSubmission data:{submission_data}\nError: {ex}")