import re


def prettify(md: str):
    # md = re.sub(r'([^\d`])(\d|\d[\d ]*\d)([^\d`])', r'\g<1>`\g<2>`\g<3>', md)
    for pat in ['`', r'**']:
        pat2 = pat.replace('*', '\\*')
        md = re.sub(pat2, f" {pat} ", md)
        md = re.sub(r' +', ' ', md)
        md = re.sub(rf"{pat2} ([^{pat2}]*) {pat2}", rf"{pat}\g<1>{pat}", md)

    md = re.sub(r' +', ' ', md)
    for pct in [':', ';', '.', '?', '!', ',', ')']:
        md = md.replace(f' {pct}', f"{pct} ")
    md = re.sub(r' +', ' ', md)
    md = md.replace('# ', '#')
    return md
