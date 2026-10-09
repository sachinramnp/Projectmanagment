from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
class Profile(models.Model):
    ROLES=[("admin","Admin"),("manager","Project Manager"),("member","Team Member")]
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    full_name=models.CharField(max_length=120)
    role=models.CharField(max_length=20,choices=ROLES,default="member")
    picture=models.ImageField(upload_to="profiles/",blank=True,null=True)
    def __str__(self): return self.full_name or self.user.username
class Project(models.Model):
    STATUSES=[("planning","Planning"),("active","Active"),("hold","On Hold"),("completed","Completed"),("archived","Archived")]
    PRIORITIES=[("low","Low"),("medium","Medium"),("high","High"),("urgent","Urgent")]
    name=models.CharField(max_length=160)
    description=models.TextField(blank=True)
    owner=models.ForeignKey(User,on_delete=models.CASCADE,related_name="owned_projects")
    status=models.CharField(max_length=20,choices=STATUSES,default="active")
    priority=models.CharField(max_length=20,choices=PRIORITIES,default="medium")
    start_date=models.DateField(blank=True,null=True)
    due_date=models.DateField(blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    is_archived=models.BooleanField(default=False)
    members=models.ManyToManyField(User,through="ProjectMembership",related_name="team_projects")
    def __str__(self): return self.name
class ProjectMembership(models.Model):
    ROLES=[("manager","Project Manager"),("member","Team Member")]
    project=models.ForeignKey(Project,on_delete=models.CASCADE)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    role=models.CharField(max_length=20,choices=ROLES,default="member")
    joined_at=models.DateTimeField(auto_now_add=True)
    class Meta: unique_together=("project","user")
class Board(models.Model):
    project=models.OneToOneField(Project,on_delete=models.CASCADE,related_name="board")
    name=models.CharField(max_length=120,default="Project Board")
    created_at=models.DateTimeField(auto_now_add=True)
class BoardColumn(models.Model):
    board=models.ForeignKey(Board,on_delete=models.CASCADE,related_name="columns")
    name=models.CharField(max_length=80)
    position=models.PositiveIntegerField(default=0)
    class Meta: ordering=["position","id"]
class Task(models.Model):
    PRIORITIES=Project.PRIORITIES
    STATUSES=[("todo","To Do"),("progress","In Progress"),("review","In Review"),("completed","Completed")]
    project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name="tasks")
    column=models.ForeignKey(BoardColumn,on_delete=models.SET_NULL,null=True,related_name="tasks")
    title=models.CharField(max_length=200); description=models.TextField(blank=True)
    assigned_to=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="assigned_tasks")
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name="created_tasks")
    priority=models.CharField(max_length=20,choices=PRIORITIES,default="medium")
    status=models.CharField(max_length=20,choices=STATUSES,default="todo")
    start_date=models.DateField(null=True,blank=True); due_date=models.DateField(null=True,blank=True)
    position=models.PositiveIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    completed_at=models.DateTimeField(null=True,blank=True)
    class Meta: ordering=["position","-created_at"]
    def __str__(self): return self.title
class Comment(models.Model):
    task=models.ForeignKey(Task,on_delete=models.CASCADE,related_name="comments")
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    content=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["created_at"]

# Phase 2 and 3 extensions. These models extend the existing Phase 1 schema.
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self): return self.message

class TaskChecklistItem(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklist_items')
    title = models.CharField(max_length=240)
    is_done = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['position', 'id']
    def __str__(self): return self.title

class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='task_attachments/%Y/%m/')
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.original_name

class ActivityLog(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activity_logs')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=80)
    details = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta: ordering = ['-created_at']
    def __str__(self): return f'{self.action} — {self.project.name}'

class ProjectTemplate(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_templates')
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    task_blueprint = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class RecurringTaskRule(models.Model):
    INTERVALS = [('daily','Daily'), ('weekly','Weekly'), ('monthly','Monthly')]
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='recurrence')
    interval = models.CharField(max_length=10, choices=INTERVALS, default='weekly')
    next_run = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return f'{self.task.title} ({self.interval})'

class TaskDependency(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependency_links')
    depends_on = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependent_links')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['task','depends_on'], name='unique_task_dependency')]
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.task_id and self.depends_on_id:
            if self.task_id == self.depends_on_id or self.task.project_id != self.depends_on.project_id:
                raise ValidationError('A task cannot depend on itself or a task in another project.')
            # Detect whether adding this edge would create a cycle.
            frontier, seen = [self.task_id], set()
            while frontier:
                current = frontier.pop()
                if current == self.depends_on_id:
                    raise ValidationError('This dependency would create a cycle.')
                if current not in seen:
                    seen.add(current)
                    frontier.extend(TaskDependency.objects.filter(depends_on_id=current).values_list('task_id', flat=True))
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
    def __str__(self): return f'{self.task} depends on {self.depends_on}'

class TimeEntry(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_entries')
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def duration_seconds(self):
        from django.utils import timezone
        end = self.ended_at or timezone.now()
        return max(0, int((end - self.started_at).total_seconds()))
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.ended_at and self.ended_at < self.started_at:
            raise ValidationError('End time must be after start time.')
    def __str__(self): return f'{self.task.title} — {self.user.username}'
