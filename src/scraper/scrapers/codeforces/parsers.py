from core.logging import log

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