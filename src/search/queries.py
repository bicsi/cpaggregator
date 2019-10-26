from elasticsearch_dsl.query import MultiMatch

from search.documents import TaskDocument


def search_task(search_query: str):
    return TaskDocument.search().query(MultiMatch(
        query=search_query, fields=TaskDocument.Django.fields)).to_queryset()