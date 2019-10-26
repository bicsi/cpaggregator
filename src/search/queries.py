from elasticsearch_dsl.query import MultiMatch

from search.documents import TaskDocument


def search_task(search_query: str):
    return TaskDocument.search().query(MultiMatch(
        query=search_query,
        fields=['name', 'source.name'])).to_queryset()