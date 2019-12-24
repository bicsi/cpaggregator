import json
import os
import re
import time

from google.cloud import translate_v3 as translate
from google.oauth2 import service_account
from html2text import html2text
from markdownx.utils import markdownify

from core import markdown
from core.logging import log

__client = None


def __get_client():
    global __client
    if __client is None:
        if 'GOOGLE_SERVICE_ACCOUNT_CRED' in os.environ:
            service_account_info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_CRED'])
        else:
            with open(f"{os.getenv('HOME')}/google_service_account_cred.json", 'r') as f:
                service_account_info = json.load(f)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info)
        __client = translate.TranslationServiceClient(credentials=credentials)
    return __client


def translate_ro_en(text: str):
    client = __get_client()
    parent = client.location_path("competitive-257117", 'global')

    html_text = markdownify(text)
    html_text = re.sub("(<h.>)[^<>]*intrare[^<>]*(</h.>)", r"\g<1><input/>\g<2>", html_text)
    html_text = re.sub("(<h.>)[^<>]*ie.ire[^<>]*(</h.>)", r"\g<1><output/>\g<2>", html_text)
    html_text = re.sub("(<h.>)[^<>]*estric[^<>]*(</h.>)", r"\g<1><constraints/>\g<2>", html_text)
    html_text = re.sub("(<h.>)[^<>]*recizar[^<>]*(</h.>)", r"\g<1><notes/>\g<2>", html_text)

    response = None
    for tries in range(3):
        try:
            response = client.translate_text(
                parent=parent,
                contents=[html_text],
                source_language_code='ro',
                target_language_code='en')
            break
        except Exception as ex:
            if tries == 2:
                raise

            if "RESOURCE_EXHAUSTED" in str(ex):
                log.warning("RESOURCE_EXHAUSTED. Sleeping for 60s...")
                time.sleep(60)

    translated = response.translations[0].translated_text
    translated = translated\
        .replace('<input/>', 'Input')\
        .replace('<output/>', 'Output')\
        .replace('<constraints/>', 'Constraints')\
        .replace('<notes/>', 'Notes')
    translated = html2text(translated)
    return markdown.prettify(translated)
