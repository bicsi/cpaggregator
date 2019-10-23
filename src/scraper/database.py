import os
from pprint import pprint

from pymongo import MongoClient, ReplaceOne
from pymongo.errors import BulkWriteError

from core.logging import log


def __insert_many_silent(coll, iterable, unique_fields):
    requests = []
    for elem in iterable:
        find_dict = {field: elem[field] for field in unique_fields}
        requests.append(ReplaceOne(find_dict, elem, upsert=True))
    try:
        result = coll.bulk_write(requests)
        return result.inserted_count
    except BulkWriteError as bwe:
        for err in bwe.details['writeErrors']:
            if err['code'] != 11000:
                log.error(bwe.details)
                log.error(pprint(iterable))
                raise
        return bwe.details['nInserted']


def get_db():
    if os.environ.get('PRODUCTION'):
        connection = MongoClient(os.environ.get('MONGODB_HOST'), int(os.environ.get('MONGODB_PORT')))
        db = connection[os.environ.get('MONGODB_NAME')]
        db.authenticate(os.environ.get('MONGODB_USER'), os.environ.get('MONGODB_PASS'))
        return db
    return MongoClient()['competitive']


def insert_report(db, report_id, created_at, report):
    coll = db["reports"]
    coll.insert({
        'report_id': report_id,
        'created_at': created_at,
        'report': report,
    })


def insert_submissions(db, submissions):
    return __insert_many_silent(
        coll=db["submissions"],
        iterable=submissions,
        unique_fields=['judge_id', 'submission_id', 'author_id'])


def insert_handles(db, handles):
    return __insert_many_silent(
        coll=db["handles"],
        iterable=handles,
        unique_fields=['judge_id', 'handle'])


def find_submissions(db, date_range=None, **query_dict):
    coll = db["submissions"]
    if date_range is not None:
        date_start, date_end = date_range
        query_dict.update({
            'submitted_on': {
                '$gte': date_start,
                '$lte':  date_end,
            }
        })
    return coll.find(query_dict)


def insert_tasks(db, tasks):
    return __insert_many_silent(
        coll=db["tasks"],
        iterable=tasks,
        unique_fields=['judge_id', 'task_id'])
