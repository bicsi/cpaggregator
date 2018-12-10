TAG_DICT = {
    'graphs': 'graphs',
    'graph matchings': 'graphs',
    'shortest paths': 'graphs',
    'bitmasks': 'bitmask',
    'constructive algorithms': 'constructive',
    'greedy': 'greedy',
    'brute force': 'brute',
    'chinese remainder theorem': 'number_theory',
    'number theory': 'number_theory',
    'math': 'math',
    'trees': 'trees',
    'data structures': 'data_structures',
    'implementation': 'implementation',
    'strings': 'strings',
    'string suffix structures': 'strings',
    'geometry': 'geometry',
    'binary search': 'search',
    'ternary search': 'search',
    'dp': 'dp',
    'flows': 'flow',
    'sortings': 'sorting',
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

    print(f"WARNING: Unknown tag: {tag_text}.")
    return None


def parse_verdict(verdict_text):
    if verdict_text in VERDICT_DICT:
        return VERDICT_DICT[verdict_text]

    print(f'WARNING: Unknown verdict: {verdict_text}.')
    return 'WA'