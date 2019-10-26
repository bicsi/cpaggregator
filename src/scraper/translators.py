import json
import os

from google.cloud import translate_v3 as translate
from google.oauth2 import service_account

from core.logging import log

__client = None


def __get_client():
    global __client
    if __client is None:
        service_account_info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_CRED'])
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info)
        __client = translate.TranslationServiceClient(credentials=credentials)
    return __client


def translate_ro_en(text: str):
    client = __get_client()
    parent = client.location_path("competitive-257117", 'global')
    response = client.translate_text(
        parent=parent,
        contents=[text],
        source_language_code='ro',
        target_language_code='en')
    return response.translations[0].translated_text
