from django.urls import path, include
from . import views

urlpatterns = [
    path('ladders/', include([
        path('rank/', views.ladders.ListLadderRank.as_view(), name='api-list-rank'),
    ])),
    path('ladder/<user>/', include([
        path('', views.ladders.ShowLadder.as_view(), name='api-show-ladder'),
        path('subs/best/', views.ladders.ListBestSubmissions.as_view(), name='api-list-subs-ladder'),
    ])),
]