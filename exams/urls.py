from django.urls import path
from .views import (
    ManageGradesView,
    VerifyRequestsView,
    CalendarView,
    ListGradesView,
    RequestReviewView,
    request_exam,
    confirmation,
)

app_name = "exams"

urlpatterns = [
    path("request-exam/", request_exam, name="request_exam"),
    path("confirmation/", confirmation, name="confirmation"),
    path("manage-grades/", ManageGradesView.as_view(), name="manage_grades"),
    path("verify-requests/", VerifyRequestsView.as_view(), name="verify_requests"),
    path("calendar/", CalendarView.as_view(), name="calendar"),
    path("calendar-edit/", CalendarView.as_view(), name="edit_calendar"),
    path("list-grades/", ListGradesView.as_view(), name="list_grades"),
    path("request-review/", RequestReviewView.as_view(), name="request_review"),
]
