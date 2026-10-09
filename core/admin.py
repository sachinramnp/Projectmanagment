from django.contrib import admin
from .models import (Profile, Project, ProjectMembership, Board, BoardColumn, Task, Comment,
    Notification, TaskChecklistItem, TaskAttachment, ActivityLog, ProjectTemplate,
    RecurringTaskRule, TaskDependency, TimeEntry)
for model in [Profile, Project, ProjectMembership, Board, BoardColumn, Task, Comment,
    Notification, TaskChecklistItem, TaskAttachment, ActivityLog, ProjectTemplate,
    RecurringTaskRule, TaskDependency, TimeEntry]:
    admin.site.register(model)
