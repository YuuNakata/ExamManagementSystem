"""
URL configuration for exam_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from .views import (
    CustomLoginView,
    dashboard_view,
    logout_view,
    notifications_view,
    notifications_count,
    notifications_list,
    mark_notification_read,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard_view, name="dashboard"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("notifications/", notifications_view, name="notifications"),
    path('api/notifications/count/', notifications_count, name='notifications_count'),
    path('api/notifications/list/',  notifications_list,  name='notifications_list'),
    path('api/notifications/read/<int:pk>/', mark_notification_read, name='notifications_read'),
    path("users/", include("users.urls")),
    path("exams/", include("exams.urls")),
    path("reports/", include("reports.urls")),
]
