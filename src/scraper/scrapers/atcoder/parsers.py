import re


def parse_title(title_text: str):
    if title_text[1:4] != " - ":
        raise Exception(f"Could not parse title {title_text}: Bad format.")
    return title_text[4:].strip()


def parse_time_limit(time_limit_text: str):
    result = re.search(r'^ *Time Limit: (\d+(\.\d+)?) sec *$', time_limit_text)
    if result is None:
        raise Exception(f"Could not parse time limit {time_limit_text}: Bad format.")
    return int(1000 * float(result.group(1)))


def parse_memory_limit(memory_limit_text: str):
    result = re.search(r'^ *Memory Limit: (\d+) MB *$', memory_limit_text)
    if result is None:
        raise Exception(f"Could not parse memory limit {memory_limit_text}: Bad format.")
    return int(result.group(1)) * 1024
