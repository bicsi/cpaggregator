import datetime
import re
from typing import List


def parse_date(date_contents: List):
    date_text = f"{date_contents[0].text} {date_contents[2].text}"
    ret = datetime.datetime.strptime(date_text, "%H:%M:%S %d %b %Y")
    return ret


def parse_memory_used(memory_used_text: str):
    value, kb = memory_used_text.rsplit(" ", 1)
    if kb != "KB":
        raise Exception(f"Expected: KB Got: {kb}")
    return int(value.replace(" ", ""))


def parse_time_exec(time_exec_text: str):
    return int(float(time_exec_text) * 1000)


def parse_verdict(verdict_text: str):
    if verdict_text == 'Compilation error':
        return 'CE'
    if verdict_text == 'Accepted':
        return 'AC'
    if verdict_text == 'Wrong answer':
        return 'WA'
    if 'runtime error' in verdict_text.lower():
        return 'RE'
    if verdict_text == "Time limit exceeded":
        return 'TLE'
    if verdict_text == "Memory limit exceeded":
        return 'MLE'
    raise Exception(f"Unknown verdict: {verdict_text}")


def parse_time_limit(time_limit_text: str):
    match = re.fullmatch(r"Time limit: ([\d.]*) second", time_limit_text)
    if not match:
        raise Exception(f"Could not parse time limit: {time_limit_text}")
    return int(1000 * float(match[1]))


def parse_memory_limit(memory_limit_text: str):
    match = re.fullmatch(r"Memory limit: ([\d.]*) MB", memory_limit_text)
    if not match:
        raise Exception(f"Could not parse memory limit: {memory_limit_text}")
    return int(float(match[1]) * 1024)
