import datetime


def parse_date(date_text: str):
    ret = datetime.datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%S Z")
    return ret


def parse_time_exec(time_exec_text: str):
    value, ms = time_exec_text.split()
    try:
        if ms != 'ms':
            raise Exception()
        value = int(value)
    except:
        raise Exception(f'Time exec not parseable: {time_exec_text}')
    return value


def parse_memory_used(memory_used_text: str):
    value, kb = memory_used_text.split()
    try:
        if kb != 'KB':
            raise Exception()
        value = int(value)
    except:
        raise Exception(f'Memory used not parseable: {memory_used_text}')
    return value


def parse_verdict(verdict_text: str):
    if verdict_text == 'Compilation error':
        return 'CE'
    a, _slash, b = verdict_text.split()
    if a == b:
        return 'AC'
    return 'WA'


def parse_score(verdict_text: str):
    if verdict_text == 'Compilation error':
        return 0
    a, _slash, b = verdict_text.split()
    # TODO: float score maybe?
    return int(round(float(a)))


def parse_time_limit(time_limit_text: str):
    return parse_time_exec(time_limit_text)


def parse_memory_limit(memory_limit_text: str):
    value, mib = memory_limit_text.split()
    try:
        if mib != 'MiB':
            raise Exception()
        value = int(value) * 1024
    except Exception as ex:
        raise Exception(f'Time exec not parseable: {memory_limit_text}', ex)
    return value
