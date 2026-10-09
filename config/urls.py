from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views
urlpatterns = [
 path("admin/", admin.site.urls), path("", views.landing, name="landing"),
 path("accounts/register/", views.register, name="register"),
 path("accounts/login/", views.login_view, name="login"),
 path("accounts/logout/", views.logout_view, name="logout"),
 path("accounts/profile/", views.profile, name="profile"),
 path("dashboard/", views.dashboard, name="dashboard"),
 path("projects/", views.projects, name="projects"),
 path("projects/new/", views.project_create, name="project_create"),
 path("projects/<int:project_id>/", views.project_detail, name="project_detail"),
 path("projects/<int:project_id>/board/", views.board, name="board"),
 path("api/", include("core.api_urls")),
]
if settings.DEBUG: urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
 path('notifications/', views.notifications_page, name='notifications'),
 path('notifications/<int:notification_id>/read/', views.notification_read, name='notification_read'),
 path('calendar/', views.calendar_view, name='calendar'),
 path('analytics/', views.analytics_view, name='analytics'),
 path('activity/', views.activity_view, name='activity'),
 path('reports/tasks.csv', views.export_tasks_csv, name='export_tasks_csv'),
 path('tasks/<int:task_id>/checklist/add/', views.add_checklist_item, name='add_checklist_item'),
 path('checklist/<int:item_id>/toggle/', views.toggle_checklist_item, name='toggle_checklist_item'),
]
