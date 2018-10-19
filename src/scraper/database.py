import os

from pymongo import MongoClient
from pymongo.errors import BulkWriteError


def __insert_many_silent(coll, iterable, **kwargs):
    try:
        return len(coll.insert_many(iterable, **kwargs).inserted_ids)
    except BulkWriteError as bwe:
        return bwe.details["nInserted"]


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
    coll = db["submissions"]
    return __insert_many_silent(coll, submissions, ordered=False)


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
    coll = db["tasks"]
    return __insert_many_silent(coll, tasks, ordered=False)
