from django.urls import path, include

from . import views, api_views

urlpatterns = [
    path('', views.LaddersDashboard.as_view(), name='dashboard'),
    path('rank/', views.LadderRankListView.as_view(), name='rank'),
    path('task/<task>/', include([
        path('', views.LadderTaskDetail.as_view(), name='ladder-task-detail'),
        path('start/', views.LadderTaskStart.as_view(), name='ladder-task-start'),
    ])),
    path('api/', include([
        path('get/<user>/', api_views.ShowLadder.as_view(), name='api-show-ladder'),
        path('get/<user>/<int:level>/', api_views.ShowLadderTask.as_view(), name='api-show-task'),
        path('rank/', api_views.ListLadderRank.as_view(), name='api-list-rank'),
    ]))
]
