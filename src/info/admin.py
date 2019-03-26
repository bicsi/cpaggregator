from django.contrib import admin
from .models import *
from markdownx.admin import MarkdownxModelAdmin

admin.site.register(TaskSheet, MarkdownxModelAdmin)
admin.site.register(Assignment)
admin.site.register(TaskSheetTask)
