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

PROJECT_ID = "competitive-257117"


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


def translate_ro_en(text: str, use_glossary=False):
    client = __get_client()
    parent = client.location_path(PROJECT_ID, 'us-central1')

    html_text = markdownify(text)
    html_text = re.sub(r"(<h.>)[^<>]*[Cc]erin[^<>]*(</h.>)", r"\g<1><task/>\g<2>", html_text)
    html_text = re.sub(r"(<h.>)[^<>]*ntrare[^<>]*(</h.>)", r"\g<1><input/>\g<2>", html_text)
    html_text = re.sub(r"(<h.>)[^<>]*e.ire[^<>]*(</h.>)", r"\g<1><output/>\g<2>", html_text)
    html_text = re.sub(r"(<h.>)[^<>]*estric[^<>]*(</h.>)", r"\g<1><constraints/>\g<2>", html_text)
    html_text = re.sub(r"(<h.>)[^<>]*reciz.r[^<>]*(</h.>)", r"\g<1><notes/>\g<2>", html_text)

    replace = {}
    for idx, code in enumerate(set(re.findall(r"<code>(.*?)<\/code>", html_text))):
        placeholder = f"<span id=\"{idx}\">0</span>"
        replace[code] = placeholder
        html_text = html_text.replace(code, placeholder)

    glossary_config = None
    if use_glossary:
        glossary = client.glossary_path(
            PROJECT_ID, 'us-central1', 'ro-en')
        glossary_config = translate.types.TranslateTextGlossaryConfig(
            glossary=glossary)
    print(glossary_config)

    response = None
    for tries in range(3):
        try:
            response = client.translate_text(
                parent=parent,
                contents=[html_text],
                source_language_code='ro',
                target_language_code='en',
                mime_type='text/html')
            break
        except Exception as ex:
            if tries == 2:
                raise

            if "RESOURCE_EXHAUSTED" in str(ex):
                log.warning("RESOURCE_EXHAUSTED. Sleeping for 60s...")
                time.sleep(60)

    translated = response.translations
    translated = translated[0].translated_text
    for code, placeholder in replace.items():
        translated = translated.replace(placeholder, code)

    translated = translated \
        .replace('<task/>', 'Task') \
        .replace('<input/>', 'Input')\
        .replace('<output/>', 'Output')\
        .replace('<constraints/>', 'Constraints')\
        .replace('<notes/>', 'Notes')
    # translated = re.sub(r"<code>[^<>]*\.in<\/code>([^\n]{1,25}<code>[^<>]*\.in<\/code>)", r"\g<1>", translated)
    # translated = re.sub(r"<code>[^<>]*\.out<\/code>([^\n]{1,25}<code>[^<>]*\.out<\/code>)", r"\g<1>", translated)
    translated = html2text(translated)
    return markdown.prettify(translated)


def sample_get_glossary(glossary_id):
    """Get Glossary"""
    client = __get_client()
    name = client.glossary_path(PROJECT_ID, "us-central1", glossary_id)

    response = client.get_glossary(name)
    print(u"Glossary name: {}".format(response.name))
    print(u"Entry count: {}".format(response.entry_count))
    print(u"Input URI: {}".format(response.input_config.gcs_source.input_uri))


def sample_list_glossaries():
    """List Glossaries"""

    client = translate.TranslationServiceClient()

    parent = client.location_path(PROJECT_ID, "us-central1")

    # Iterate over all results
    for glossary in client.list_glossaries(parent):
        print('Name: {}'.format(glossary.name))
        print('Entry count: {}'.format(glossary.entry_count))
        print('Input uri: {}'.format(
            glossary.input_config.gcs_source.input_uri))
        for language_code in glossary.language_codes_set.language_codes:
            print('Language code: {}'.format(language_code))
        if glossary.language_pair:
            print(glossary.language_pair.source_language_code)
            print(glossary.language_pair.target_language_code)


def sample_create_glossary(input_file, glossary_id):
    input_uri = f"gs://competitive-heroku/{input_file}"
    """Create Glossary"""
    client = __get_client()
    location = 'us-central1'  # The location of the glossary

    name = client.glossary_path(
        PROJECT_ID,
        location,
        glossary_id)
    language_codes_set = translate.types.Glossary.LanguageCodesSet(
        language_codes=['ro', 'en'])

    gcs_source = translate.types.GcsSource(
       input_uri=input_uri)

    input_config = translate.types.GlossaryInputConfig(
        gcs_source=gcs_source)

    glossary = translate.types.Glossary(
        name=name,
        language_codes_set=language_codes_set,
        input_config=input_config)

    parent = client.location_path(PROJECT_ID, location)

    operation = client.create_glossary(parent=parent, glossary=glossary)

    result = operation.result(timeout=90)
    print('Created: {}'.format(result.name))
    print('Input Uri: {}'.format(result.input_config.gcs_source.input_uri))


def sample_delete_glossary(glossary_id):
    """Delete Glossary"""
    client = __get_client()

    # TODO(developer): Uncomment and set the following variables
    # project_id = 'YOUR_PROJECT_ID'
    # glossary_id = 'GLOSSARY_ID'

    parent = client.glossary_path(
        PROJECT_ID,
        'us-central1',
        glossary_id)

    operation = client.delete_glossary(parent)
    result = operation.result(timeout=90)
    print('Deleted: {}'.format(result.name))
