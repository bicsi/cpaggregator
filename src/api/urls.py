from django.urls import path, include
from . import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('ladders/', include([
        path('rank/', views.ladders.ListLadderRank.as_view(), name='api-list-rank'),
    ])),
    path('me/', views.base.RetrieveCurrentUser.as_view(), name='api-me'),
    path('judges/', views.base.ListJudges.as_view(), name='api-judges'),
    path('user/<user>/', include([
        path('', views.base.RetrieveUser.as_view(), name='api-user'),
        path('subs/best/', views.base.ListUserBestSubmissions.as_view(), name='api-list-subs-ladder'),
        path('ladder/', include([
            path('', views.ladders.ShowLadder.as_view(), name='api-show-ladder'),
            path('start/', views.ladders.StartTask.as_view(), name='api-start-task'),
            path('subs/best/', views.ladders.ListBestSubmissions.as_view(), name='api-list-subs-ladder'),
        ])),
    ])),
]