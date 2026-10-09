from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q,Count
from django.utils import timezone
from .models import Profile,Project,ProjectMembership,Board,BoardColumn,Task,Comment
from .permissions import can_access_project
def landing(request): return redirect("dashboard") if request.user.is_authenticated else render(request,"landing.html")
def register(request):
    if request.user.is_authenticated:return redirect("dashboard")
    if request.method=="POST":
        name=request.POST.get("name","").strip(); email=request.POST.get("email","").strip().lower(); password=request.POST.get("password","")
        if not name or not email or len(password)<8: messages.error(request,"Enter your name, valid email, and password (at least 8 characters).")
        elif User.objects.filter(email__iexact=email).exists(): messages.error(request,"An account with this email already exists.")
        else:
            username=email
            u=User.objects.create_user(username=username,email=email,password=password,first_name=name[:150])
            u.profile.full_name=name;u.profile.save();login(request,u);return redirect("dashboard")
    return render(request,"auth.html",{"mode":"register"})
def login_view(request):
    if request.user.is_authenticated:return redirect("dashboard")
    if request.method=="POST":
        email=request.POST.get("email","").strip().lower(); password=request.POST.get("password","")
        u=authenticate(request,username=email,password=password)
        if u:login(request,u);return redirect("dashboard")
        messages.error(request,"Email or password is incorrect.")
    return render(request,"auth.html",{"mode":"login"})
@login_required
def logout_view(request):
    if request.method=="POST":logout(request)
    return redirect("login")
@login_required
def profile(request):
    p=request.user.profile
    if request.method=="POST":
        p.full_name=request.POST.get("full_name",p.full_name).strip() or p.full_name
        p.picture=request.FILES.get("picture",p.picture);p.save()
        request.user.email=request.POST.get("email",request.user.email).strip();request.user.save()
        messages.success(request,"Profile updated.")
    return render(request,"profile.html",{"profile":p})
def visible_projects(user):return Project.objects.filter(Q(owner=user)|Q(members=user)).distinct()
@login_required
def dashboard(request):
    projects=visible_projects(request.user);tasks=Task.objects.filter(project__in=projects)
    today=timezone.localdate()
    return render(request,"dashboard.html",{"projects":projects.order_by("-updated_at")[:6],"total_projects":projects.count(),"active_projects":projects.filter(status="active").count(),"completed_projects":projects.filter(status="completed").count(),"total_tasks":tasks.count(),"pending":tasks.exclude(status="completed").count(),"completed_tasks":tasks.filter(status="completed").count(),"overdue":tasks.filter(due_date__lt=today).exclude(status="completed").count(),"upcoming":tasks.filter(due_date__gte=today).exclude(status="completed").order_by("due_date")[:6],"recent":tasks.order_by("-updated_at")[:6]})
@login_required
def projects(request):
    qs=visible_projects(request.user)
    q=request.GET.get("q","").strip()
    status=request.GET.get("status","")
    if q:qs=qs.filter(Q(name__icontains=q)|Q(description__icontains=q))
    if status:qs=qs.filter(status=status)
    return render(request,"projects.html",{"projects":qs.order_by("-updated_at"),"q":q,"status":status})
@login_required
def project_create(request):
    if request.method=="POST":
        p=Project.objects.create(name=request.POST.get("name","").strip(),description=request.POST.get("description",""),owner=request.user,status=request.POST.get("status","active"),priority=request.POST.get("priority","medium"),due_date=request.POST.get("due_date") or None)
        ProjectMembership.objects.get_or_create(project=p,user=request.user,defaults={"role":"manager"})
        b=Board.objects.create(project=p)
        for i,n in enumerate(["To Do","In Progress","In Review","Completed"]):BoardColumn.objects.create(board=b,name=n,position=i)
        messages.success(request,"Project created.");return redirect("project_detail",project_id=p.id)
    return render(request,"project_form.html")
@login_required
def project_detail(request,project_id):
    p=get_object_or_404(visible_projects(request.user),id=project_id)
    return render(request,"project_detail.html",{"project":p,"tasks":p.tasks.select_related("assigned_to","column").order_by("due_date"),"members":User.objects.filter(team_projects=p)})
@login_required
def board(request,project_id):
    p=get_object_or_404(visible_projects(request.user),id=project_id)
    b,created=Board.objects.get_or_create(project=p)
    if created:
        for i,n in enumerate(["To Do","In Progress","In Review","Completed"]):BoardColumn.objects.create(board=b,name=n,position=i)
    columns=b.columns.prefetch_related("tasks").all()
    if request.method=="POST":
        action=request.POST.get("action")
        if action=="create_task":
            col=get_object_or_404(columns,id=request.POST.get("column"))
            Task.objects.create(project=p,column=col,title=request.POST.get("title","").strip(),description=request.POST.get("description",""),assigned_to_id=request.POST.get("assigned_to") or None,created_by=request.user,priority=request.POST.get("priority","medium"),status={"To Do":"todo","In Progress":"progress","In Review":"review","Completed":"completed"}.get(col.name,"todo"),due_date=request.POST.get("due_date") or None,position=col.tasks.count())
        elif action=="move":
            task=get_object_or_404(p.tasks,id=request.POST.get("task"));col=get_object_or_404(columns,id=request.POST.get("column"))
            task.column=col;task.status={"To Do":"todo","In Progress":"progress","In Review":"review","Completed":"completed"}.get(col.name,"todo");task.save()
        return redirect("board",project_id=p.id)
    return render(request,"board.html",{"project":p,"columns":columns,"members":User.objects.filter(team_projects=p)})

# Phase 2/3 pages and actions
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.db.models import Sum
from datetime import date
from .models import Notification, TaskChecklistItem, TaskAttachment, ActivityLog, ProjectTemplate, RecurringTaskRule, TaskDependency, TimeEntry

@login_required
def notifications_page(request):
    items = Notification.objects.filter(recipient=request.user)[:100]
    return render(request, 'notifications.html', {'notifications': items})

@login_required
@require_POST
def notification_read(request, notification_id):
    item = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    item.is_read = True
    item.save(update_fields=['is_read'])
    return redirect(item.link or 'notifications')

@login_required
def calendar_view(request):
    projects = visible_projects(request.user)
    tasks = Task.objects.filter(project__in=projects).select_related('project','assigned_to').exclude(due_date__isnull=True).order_by('due_date')
    return render(request, 'calendar.html', {'tasks': tasks})

@login_required
def analytics_view(request):
    projects = visible_projects(request.user)
    tasks = Task.objects.filter(project__in=projects)
    today = timezone.localdate()
    return render(request, 'analytics.html', {
        'total': tasks.count(), 'completed': tasks.filter(status='completed').count(),
        'pending': tasks.exclude(status='completed').count(),
        'overdue': tasks.filter(due_date__lt=today).exclude(status='completed').count(),
        'projects': projects.count(),
    })

@login_required
def activity_view(request):
    projects = visible_projects(request.user)
    return render(request, 'activity.html', {'activities': ActivityLog.objects.filter(project__in=projects).select_related('project','task','actor')[:100]})

@login_required
def export_tasks_csv(request):
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="project_tasks.csv"'
    writer = csv.writer(response)
    writer.writerow(['Project','Task','Status','Priority','Assignee','Start date','Due date'])
    projects = visible_projects(request.user)
    for task in Task.objects.filter(project__in=projects).select_related('project','assigned_to'):
        writer.writerow([task.project.name, task.title, task.get_status_display(), task.priority, task.assigned_to.username if task.assigned_to else '', task.start_date or '', task.due_date or ''])
    return response

@login_required
@require_POST
def add_checklist_item(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if not can_access_project(request.user, task.project): return HttpResponseForbidden('Not allowed')
    title = request.POST.get('title','').strip()
    if title:
        TaskChecklistItem.objects.create(task=task, title=title[:240], created_by=request.user)
        ActivityLog.objects.create(project=task.project, task=task, actor=request.user, action='checklist_added', details=title[:450])
    return redirect('board', project_id=task.project_id)

@login_required
@require_POST
def toggle_checklist_item(request, item_id):
    item = get_object_or_404(TaskChecklistItem, id=item_id)
    if not can_access_project(request.user, item.task.project): return HttpResponseForbidden('Not allowed')
    item.is_done = not item.is_done
    item.save(update_fields=['is_done'])
    return redirect('board', project_id=item.task.project_id)
