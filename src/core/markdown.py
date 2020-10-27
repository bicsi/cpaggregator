import re
from markdownx.utils import markdownify
from html2text import html2text as base_html2text


def prettify(md: str):
    # md = re.sub(r'([^\d`])(\d|\d[\d ]*\d)([^\d`])', r'\g<1>`\g<2>`\g<3>', md)
    for pat in ['`', r'**']:
        pat2 = pat.replace('*', '\\*')
        md = re.sub(pat2, f" {pat} ", md)
        md = re.sub(r' +', ' ', md)
        md = re.sub(rf"{pat2} ([^{pat2}]*) {pat2}", rf"{pat}\g<1>{pat}", md)

    md = md.replace("* _", "*_").replace("_ *", "_*")

    md = re.sub(r' +', ' ', md)
    for pct in [':', ';', '.', '?', '!', ',', ')']:
        md = md.replace(f' {pct}', f"{pct} ")
    md = re.sub(r' +', ' ', md)
    # md = md.replace('# ', '#')
    return md


def text2html(md: str):
    text = markdownify(md)
    text = text.replace('\\$', '[[DOLLAR]]')
    text = re.sub(r'\$((.*?)[^\\])\$', '<latex>\g<1></latex>', text)
    text = text.replace('[[DOLLAR]]', '$')
    return text


def html2text(html: str):
    html = html.replace('$', '\\$')
    html = re.sub(r'<latex>(.*?)</latex>', '<code>$\g<0>$</code>', html)
    md = base_html2text(html, bodywidth=0)
    md = re.sub(r'#\s+', '# ', md)
    md = re.sub(r'`\$(.*?)\$`', '$\g<1>$', md)
    return md