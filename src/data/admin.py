from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Judge)
admin.site.register(Task)
admin.site.register(Submission)
admin.site.register(UserProfile)
admin.site.register(UserHandle)
admin.site.register(UserGroup)
