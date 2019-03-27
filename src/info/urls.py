"""cpaggregator URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from info import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('rank/', views.RankListView.as_view(), name='rank-list'),
    path('group/', views.GroupListView.as_view(), name='group-list'),
    path('group/<group_id>/', include([
        path('', views.GroupDetailView.as_view(), name='group-detail'),
        path('join/', views.GroupJoinView.as_view(), name='group-join'),
        path('leave/', views.GroupLeaveView.as_view(), name='group-leave'),
        path('update/', views.GroupUpdateView.as_view(), name='group-update'),
        path('delete-member/', views.GroupMemberDeleteView.as_view(), name='group-member-delete'),
        path('add-member/', views.GroupMemberAddView.as_view(), name='group-member-add'),
        path('create-assignment/', views.AssignmentCreateView.as_view(), name='assignment-create'),
        path('sheet/<sheet_id>/', include([
                path('', views.ResultsDetailView.as_view(
                    show_results=False,
                    show_submissions=True,
                ), name='group-sheet-detail'),
                path('results/', views.ResultsDetailView.as_view(
                    show_results=True,
                    show_submissions=False,
                ), name='group-sheet-results'),
                path('submissions/', views.ResultsDetailView.as_view(
                    show_results=False,
                    show_submissions=True,
                ), name='group-sheet-submissions'),
            ])),
        path('reorder-assignments/', views.UpdateGroupAssignmentOrdering.as_view(),
             name='group-assignment-reorder'),
        path('delete/', views.GroupDeleteView.as_view(), name='group-delete'),
    ])),
    path('create-group/', views.GroupCreateView.as_view(), name='group-create'),
    path('create-sheet/', views.SheetCreateView.as_view(), name='sheet-create'),
    path('sheet/<sheet_id>/', include([
        path('', views.SheetDetailView.as_view(), name='sheet-detail'),
        path('add-task/', views.SheetTaskAddView.as_view(), name='sheet-task-add'),
        path('delete-task/', views.SheetTaskDeleteView.as_view(), name='sheet-task-delete'),
        path('delete/', views.SheetDeleteView.as_view(), name='sheet-delete'),
        path('update-description/', views.SheetDescriptionUpdateView.as_view(),
             name='sheet-description-update'),
        path('reorder-tasks/', views.UpdateSheetTaskOrdering.as_view(),
             name='sheet-task-reorder')
    ])),
    path('task/', include([
        path('', views.TaskListView.as_view(), name='task-list'),
        path('<judge_id>/<task_id>/', include([
            path('', views.TaskDetailView.as_view(), name='task-detail'),
            path('favorite/', views.FavoriteToggleView.as_view(), name='task-favorite'),
        ])),
    ])),
    path('me/', views.MeDetailView.as_view(), name='me'),
    path('handle/<handle_id>/delete/', views.HandleDeleteView.as_view(), name='delete-handle'),
    path('handle/create/', views.HandleCreateView.as_view(), name='handle-create'),
    path('profile/<username>/update/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/<username>/', views.UserSubmissionsDetailView.as_view(), name='profile'),
]
