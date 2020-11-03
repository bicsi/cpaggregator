from django.urls import path, include
from . import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('accounts/', include('rest_registration.api.urls')),
    path('token/', views.token.TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('token/refresh/', views.token.TokenRefreshView.as_view(), name='token_refresh'),
    path('ladders/', include([
        path('rank/', views.ladders.ListLadderRank.as_view(), name='api-list-rank'),
    ])),
    path('group/', include([
        path('', views.group.ListGroups.as_view()),
        path('<group>/', include([
            path('', views.group.RetrieveGroup.as_view()),
            path('member/<username>/',
                 views.group.RetrieveDestroyGroupMember.as_view()),
            path('member/', views.group.ListCreateGroupMember.as_view()),
            path('assignments/', views.group.ListAssignments.as_view()),
        ])),
    ])),
    path('task/', include([
        path('<task-path:task_path>/', include([
            path('', views.task.RetrieveTask.as_view()),
        ])),
    ])),
    path('me/', views.profile.RetrieveCurrentUser.as_view(), name='api-me'),
    path('handle/', views.profile.CreateHandle.as_view()),
    path('handle/<judge_id>/<handle>/',
         views.profile.RetrieveDestroyHandle.as_view()),
    path('judges/', views.base.ListJudges.as_view(), name='api-judges'),
    path('users/rank/', views.profile.ListUserRank.as_view(), name='api-user-rank'),
    path('status/', include([
        path('best/', views.submissions.ListSubmissions.as_view(kind='best')),
        path('solved/', views.submissions.ListSubmissions.as_view(kind='solved')),
        path('unsolved/', views.submissions.ListSubmissions.as_view(kind='unsolved')),
    ])),
    path('user/<user>/', include([
        path('', views.profile.RetrieveUser.as_view(), name='api-user'),
        path('subs/', include([
            path('best/', views.base.ListUserBestSubmissions.as_view(),
                 name='api-list-subs-ladder'),
            path('solved/', views.base.ListUserBestSubmissions.as_view(filter_ac=True),
                 name='api-list-subs-ladder-ac'),
            path('unsolved/', views.base.ListUserBestSubmissions.as_view(exclude_ac=True),
                 name='api-list-subs-ladder-nac'),
        ])),
        path('ladder/', include([
            path('', views.ladders.ShowLadder.as_view(), name='api-show-ladder'),
            path('start/', views.ladders.StartTask.as_view(),
                 name='api-start-task'),
            path('subs/best/', views.ladders.ListBestSubmissions.as_view(),
                 name='api-list-subs-ladder'),
        ])),
    ])),
]
