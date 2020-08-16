from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.LaddersDashboard.as_view(), name='dashboard'),
    path('task/<task>/', include([
        path('', views.LadderTaskDetail.as_view(), name='ladder-task-detail'),
        path('start/', views.LadderTaskStart.as_view(), name='ladder-task-start'),
    ])),
]
