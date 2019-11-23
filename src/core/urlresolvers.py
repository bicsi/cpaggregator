

def get_handle_url(judge_id: str, handle: str):
    if judge_id == 'ojuz':
        return f"https://oj.uz/profile/{handle}"
    if judge_id == 'csa':
        if handle.startswith('_uid_'):
            return f"https://csacademy.com/userid/{handle[5:]}"
        return f"https://csacademy.com/user/{handle}"
    if judge_id == 'ia':
        return f"https://www.infoarena.ro/utilizator/{handle}"
    if judge_id == 'cf':
        return f"https://codeforces.com/profile/{handle}"
    if judge_id == 'ac':
        return f"https://atcoder.jp/users/{handle}"


def get_submission_url(judge_id: str, task_id: str, submission_id: str):
    if judge_id == 'ojuz':
        return f'https://oj.uz/submission/{submission_id}'
    if judge_id == 'csa':
        return f'https://csacademy.com/submission/{submission_id}'
    if judge_id == 'ia':
        return f'https://www.infoarena.ro/job_detail/{submission_id}'
    if judge_id == 'cf':
        contest_id, _ = task_id.split('_')
        if int(contest_id) >= 100000:
            return f'https://codeforces.com/gym/{contest_id}/submission/{submission_id}'
        else:
            return f'https://codeforces.com/contest/{contest_id}/submission/{submission_id}'
    if judge_id == 'ac':
        contest_id, _ = task_id.rsplit('_', 1)
        return f'https://atcoder.jp/contests/{contest_id.replace("_", "-")}/submissions/{submission_id}'


def get_task_url(judge_id, task_id):
    if judge_id == 'ojuz':
        return 'https://oj.uz/problem/view/%s' % task_id
    if judge_id == 'csa':
        return 'https://csacademy.com/contest/archive/task/%s' % task_id
    if judge_id == 'ia':
        return 'https://www.infoarena.ro/problema/%s' % task_id
    if judge_id == 'cf':
        contest_id, task_letter = task_id.split('_')
        if int(contest_id) >= 100000:
            return f'https://codeforces.com/gym/{contest_id}/problem/{task_letter.upper()}'
        else:
            return f'https://codeforces.com/problemset/problem/{contest_id}/{task_letter.upper()}'
    if judge_id == 'ac':
        contest_id, _ = task_id.rsplit('_', 1)
        return f"https://atcoder.jp/contests/{contest_id.replace('_', '-')}/tasks/{task_id}"