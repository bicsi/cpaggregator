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

from django.urls import path, include, register_converter

from info import views


class TaskPathConverter:
    regex = "((cf|ac)/([^/]+)/([^/]+))|" \
            "((ia|ojuz|csa)/([^/]+))"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)


register_converter(TaskPathConverter, "task-path")

urlpatterns = [
    path('dashboard/', views.dashboard.DashboardView.as_view(), name='dashboard'),
    path('rank/', views.dashboard.RankListView.as_view(), name='rank-list'),
    path('group/', views.group.GroupListView.as_view(), name='group-list'),
    path('group/<group_id>/', include([
        path('', views.group.GroupDetailView.as_view(), name='group-detail'),
        path('join/', views.group.GroupJoinView.as_view(), name='group-join'),
        path('leave/', views.group.GroupLeaveView.as_view(), name='group-leave'),
        path('update/', views.group.GroupUpdateView.as_view(), name='group-update'),
        path('change-role/', views.group.GroupMemberRoleChange.as_view(), name='group-member-role-change'),
        path('delete-member/', views.group.GroupMemberDeleteView.as_view(), name='group-member-delete'),
        path('add-member/', views.group.GroupMemberAddView.as_view(), name='group-member-add'),
        path('create-assignment/', views.group.AssignmentCreateView.as_view(), name='assignment-create'),
        path('results/', views.group.GroupDetailView.as_view(view_results=True), name='group-results'),
        path('sheet/<sheet_id>/', include([
                path('', views.sheet.ResultsDetailView.as_view(
                    show_results=True,
                    show_submissions=False,
                ), name='group-sheet-detail'),
                path('update/', views.sheet.AssignmentUpdateView.as_view(),
                     name='assignment-update'),
                path('results/', views.sheet.ResultsDetailView.as_view(
                    show_results=True,
                    show_submissions=False,
                ), name='group-sheet-results'),
                path('submissions/', views.sheet.ResultsDetailView.as_view(
                    show_results=False,
                    show_submissions=True,
                ), name='group-sheet-submissions'),
                path('download/', views.sheet.DownloadResultsView.as_view(),
                     name='group-sheet-results-download'),
            ])),
        path('reorder-assignments/', views.group.GroupAssignmentOrderingUpdate.as_view(),
             name='group-assignment-reorder'),
        path('delete/', views.group.GroupDeleteView.as_view(), name='group-delete'),
    ])),
    path('create-group/', views.group.GroupCreateView.as_view(), name='group-create'),
    path('create-sheet/', views.sheet.SheetCreateView.as_view(), name='sheet-create'),
    path('sheet/<sheet_id>/', include([
        path('', views.sheet.SheetDetailView.as_view(), name='sheet-detail'),
        path('task/add/', views.sheet.SheetTaskAddView.as_view(), name='sheet-task-add'),
        path('task/<task_id>/edit/', views.sheet.SheetTaskEditView.as_view(), name='sheet-task-edit'),
        path('task/<task_id>/delete/', views.sheet.SheetTaskDeleteView.as_view(), name='sheet-task-delete'),
        path('delete/', views.sheet.SheetDeleteView.as_view(), name='sheet-delete'),
        path('description/update/', views.sheet.SheetDescriptionUpdateView.as_view(),
             name='sheet-description-update'),
        path('task/reorder/', views.sheet.SheetTaskOrderingUpdate.as_view(),
             name='sheet-task-reorder')
    ])),
    path('task/', include([
        path('', views.task.TaskListView.as_view(), name='task-list'),
        path('<task-path:task_path>/', include([
            path('', views.task.TaskDetailView.as_view(), name='task-detail'),
            path('favorite/', views.task.FavoriteToggleView.as_view(), name='task-favorite'),
            path('preview/', views.task.TaskPreviewView.as_view(), name='task-preview'),
            path('create-tag/', views.task.TagCreateView.as_view(), name='task-tag-create'),
            path('tag/<tag_name>/delete', views.task.TagDeleteView.as_view(), name='task-tag-delete'),
            path('update/', views.task.TaskStatementUpdateView.as_view(), name='task-statement-update'),
            path('stm-scrape/', views.task.TaskStatementScrapeView.as_view(), name='task-statement-scrape'),
            path('sub-scrape/', views.task.TaskSubmissionsScrapeView.as_view(), name='task-submissions-scrape'),
        ])),
    ])),
    path('status/', include([
        path('', views.submission.SubmissionListView.as_view(), name='submission-list'),
        path('download/', views.submission.AllSubmissionsDownloadCSVView.as_view(), name='submissions-download'),
    ])),
    path('me/', views.profile.MeDetailView.as_view(), name='me'),
    path('handle/<handle_id>/delete/', views.profile.HandleDeleteView.as_view(), name='delete-handle'),
    path('handle/create/', views.profile.HandleCreateView.as_view(), name='handle-create'),
    path('profile/<username>/update/', views.profile.ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/<username>/', views.profile.UserSubmissionsDetailView.as_view(), name='profile'),
]
