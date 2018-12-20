from django.urls import path
from . import views

urlpatterns = [
    path('feedback/', views.FeedbackCreateView.as_view(), name='feedback-create'),
]