from rest_framework.routers import DefaultRouter
from django.urls import path,include
from .api import ProjectViewSet,TaskViewSet,CommentViewSet,ColumnViewSet,dashboard_api
router=DefaultRouter()
router.register("projects",ProjectViewSet,basename="project")
router.register("tasks",TaskViewSet,basename="task")
router.register("comments",CommentViewSet,basename="comment")
router.register("columns",ColumnViewSet,basename="column")
urlpatterns=[path("dashboard/",dashboard_api),path("",include(router.urls))]
