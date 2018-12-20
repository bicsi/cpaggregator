from django.db import models

# Create your models here.
from data.models import UserProfile


class FeedbackMessage(models.Model):
    author = models.ForeignKey(UserProfile, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=256)
    content = models.TextField()

    def __str__(self):
        return self.title
