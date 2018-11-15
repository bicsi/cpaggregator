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
    path('sheet/<sheet_id>/', include([
        path('', views.ResultsDetailView.as_view(), name='sheet-results'),
        path('all/', views.ResultsDetailView.as_view(show_all=True), name='sheet-results-all'),
        path('add-task/', views.SheetTaskCreateView.as_view(), name='sheet-task-add'),
        path('delete/', views.SheetDeleteView.as_view(), name='sheet-delete'),
    ])),
    path('group/<group_id>/', include([
        path('', views.GroupDetailView.as_view(), name='group-detail'),
        path('delete-member', views.GroupMemberDeleteView.as_view(), name='group-member-delete'),
        path('add-member', views.GroupMemberCreateView.as_view(), name='group-member-add'),
        path('create-sheet', views.SheetCreateView.as_view(), name='sheet-create'),
    ])),
    path('me/', views.MeDetailView.as_view(), name='me'),
    path('handle/<handle_id>/delete', views.HandleDeleteView.as_view(), name='delete-handle'),
    path('handle/create', views.HandleCreateView.as_view(), name='create-handle'),
    path('profile/<username>/', views.UserSubmissionsDetailView.as_view(), name='profile'),
    path('profile/<username>/update/', views.ProfileUpdateView.as_view(), name='update-profile'),
]
