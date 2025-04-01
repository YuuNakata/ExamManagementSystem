from django.urls import path
from . import views

app_name = "exams"

urlpatterns = [
    path("manage-grades/", views.manage_grades, name="manage_grades"),
    path("verify-requests/", views.verify_requests, name="verify_requests"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("list-grades/", views.list_grades, name="list_grades"),
    path("request-review/", views.request_review, name="request_review"),
    path("edit-calendar/", views.edit_calendar, name="edit_calendar"),
    path("edit-exam/<int:pk>/", views.update_exam, name="edit_exam"),
    path("create-exam/", views.create_exam, name="create_exam"),
    path("request-exam/", views.request_exam, name="request_exam"),
    path("calendar/", views.calendar_view, name="calendar"),
]
