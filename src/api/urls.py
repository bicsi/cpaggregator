from django.urls import path, include
from . import views

urlpatterns = [
    path('ladders/', include([
        path('rank/', views.ladders.ListLadderRank.as_view(), name='api-list-rank'),
    ])),
    path('user/<user>/', include([
        path('ladder/', include([
            path('', views.ladders.ShowLadder.as_view(), name='api-show-ladder'),
            path('subs/best/', views.ladders.ListBestSubmissions.as_view(), name='api-list-subs-ladder'),
        ])),
        path('subs/best/', views.submissions.ListBestSubmissions.as_view(), name='api-list-subs'),
    ]))
]