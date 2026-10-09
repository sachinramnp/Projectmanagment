from rest_framework import viewsets,status
from rest_framework.decorators import action,api_view,permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.db.models import Q
from .models import Project,ProjectMembership,Board,BoardColumn,Task,Comment
from .serializers import ProjectSerializer,ColumnSerializer,TaskSerializer,CommentSerializer,UserBrief
from .permissions import can_access_project
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class=ProjectSerializer
    def get_queryset(self):
        u=self.request.user
        return Project.objects.filter(Q(owner=u)|Q(members=u)).distinct().order_by("-updated_at")
    def perform_update(self,serializer):
        if self.get_object().owner_id!=self.request.user.id and not self.request.user.is_superuser:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only the project owner can edit project settings.")
        serializer.save()
    def perform_destroy(self,instance):
        if instance.owner_id!=self.request.user.id and not self.request.user.is_superuser:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only the project owner can delete this project.")
        instance.delete()
    @action(detail=True,methods=["get","post"],url_path="members")
    def members(self,request,pk=None):
        p=self.get_object()
        if request.method=="GET": return Response(UserBrief(User.objects.filter(team_projects=p),many=True).data)
        if p.owner_id!=request.user.id and not request.user.is_superuser: return Response({"detail":"Owner permission required."},status=403)
        uid=request.data.get("user_id")
        try: u=User.objects.get(pk=uid)
        except (User.DoesNotExist,ValueError,TypeError): return Response({"detail":"Valid user_id required."},status=400)
        ProjectMembership.objects.get_or_create(project=p,user=u,defaults={"role":request.data.get("role","member")})
        return Response({"status":"member added"},status=201)
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class=TaskSerializer
    def get_queryset(self):
        u=self.request.user
        qs=Task.objects.filter(Q(project__owner=u)|Q(project__members=u)).distinct()
        p=self.request.query_params.get("project")
        if p: qs=qs.filter(project_id=p)
        q=self.request.query_params.get("search")
        if q: qs=qs.filter(Q(title__icontains=q)|Q(description__icontains=q))
        for field in ["status","priority","assigned_to"]:
            value=self.request.query_params.get(field)
            if value: qs=qs.filter(**{field:value})
        return qs.select_related("project","column","assigned_to")
    def perform_create(self,serializer):
        p=serializer.validated_data["project"]
        if not can_access_project(self.request.user,p): from rest_framework.exceptions import PermissionDenied; raise PermissionDenied()
        serializer.save(created_by=self.request.user)
    def perform_update(self,serializer):
        from rest_framework.exceptions import PermissionDenied
        p=serializer.validated_data.get("project",self.get_object().project)
        if not can_access_project(self.request.user,p): raise PermissionDenied()
        serializer.save()
    @action(detail=True,methods=["patch"])
    def move(self,request,pk=None):
        task=self.get_object()
        col_id=request.data.get("column_id")
        try: col=BoardColumn.objects.get(pk=col_id,board__project=task.project)
        except BoardColumn.DoesNotExist: return Response({"detail":"Invalid column."},status=400)
        task.column=col; task.status={"To Do":"todo","In Progress":"progress","In Review":"review","Completed":"completed"}.get(col.name,task.status)
        task.position=int(request.data.get("position",0)); task.save()
        return Response(TaskSerializer(task).data)
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class=CommentSerializer
    def get_queryset(self):
        u=self.request.user
        return Comment.objects.filter(Q(task__project__owner=u)|Q(task__project__members=u)).distinct()
    def perform_create(self,serializer):
        task=serializer.validated_data["task"]
        if not can_access_project(self.request.user,task.project):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()
        serializer.save(user=self.request.user)
    def perform_update(self,serializer):
        from rest_framework.exceptions import PermissionDenied
        if self.get_object().user_id!=self.request.user.id: raise PermissionDenied("You can edit only your own comments.")
        serializer.save()
    def perform_destroy(self,instance):
        from rest_framework.exceptions import PermissionDenied
        if instance.user_id!=self.request.user.id and not self.request.user.is_superuser: raise PermissionDenied()
        instance.delete()
class ColumnViewSet(viewsets.ModelViewSet):
    serializer_class=ColumnSerializer
    def get_queryset(self):
        return BoardColumn.objects.filter(board__project__in=Project.objects.filter(Q(owner=self.request.user)|Q(members=self.request.user))).distinct()
    def perform_create(self,serializer):
        board=Board.objects.get(pk=self.request.data.get("board"),project__in=Project.objects.filter(Q(owner=self.request.user)|Q(members=self.request.user)))
        serializer.save(board=board)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    tasks=TaskViewSet.as_view({"get":"list"})
    from .serializers import TaskSerializer
    projects=Project.objects.filter(Q(owner=request.user)|Q(members=request.user)).distinct()
    qs=Task.objects.filter(project__in=projects)
    return Response({"projects":projects.count(),"active_projects":projects.filter(status="active").count(),"completed_projects":projects.filter(status="completed").count(),"tasks":qs.count(),"pending":qs.exclude(status="completed").count(),"completed_tasks":qs.filter(status="completed").count(),"tasks_by_status":{s:qs.filter(status=s).count() for s,_ in Task.STATUSES}})
