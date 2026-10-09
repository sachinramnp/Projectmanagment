from rest_framework.permissions import BasePermission
from .models import ProjectMembership
def can_access_project(user, project):
    return user.is_authenticated and (user.is_superuser or project.owner_id==user.id or ProjectMembership.objects.filter(project=project,user=user).exists())
class ProjectAccess(BasePermission):
    def has_object_permission(self,request,view,obj):
        project=getattr(obj,"project",obj)
        return can_access_project(request.user,project)
