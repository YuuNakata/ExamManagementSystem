# --- START OF FILE urls.py ---

from django.urls import path
from . import views

app_name = "exams"

urlpatterns = [
    # Student URLs
    path("request-exam/", views.request_exam, name="request_exam"),
    path(
        "submit-request/", views.submit_exam_request, name="submit_exam_request"
    ),  # New URL for submitting request
    path(
        "edit-calendar/", views.edit_calendar, name="edit_calendar"
    ),  # Teacher's calendar view
    path(
        "edit-exam/<int:pk>/", views.update_exam, name="edit_exam"
    ),  # Action URL for updating
    path("create-exam/", views.create_exam, name="create_exam"),
    path("delete-exam/<int:pk>/", views.delete_exam, name="delete_exam"),
    path("verify-requests/", views.verify_requests_fbv, name="verify_requests"),
    # URLs for Grade Management by Professors
    path("manage-grades/", views.manage_grades_list_fbv, name="manage_grades"),
    path(
        "grade-exam/<int:pk>/", views.grade_exam_request_fbv, name="grade_exam_request"
    ),
    # URL for Students to View Their Grades
    path("my-grades/", views.list_my_grades_fbv, name="my_grades"),
    # URLs for Review Requests
    path("request-review/", views.request_review, name="request_review"),
    path(
        "submit-review-request/",
        views.submit_review_request,
        name="submit_review_request",
    ),
    path(
        "approve-request/<int:pk>/", views.approve_request_fbv, name="approve_request"
    ),  # Acción Aprobar - Updated to FBV
    path(
        "reject-request/<int:pk>/", views.reject_request_fbv, name="reject_request"
    ),  # Acción Rechazar - Updated to FBV
    # Generic Calendar URL - remove or make it redirect based on role if needed
    path("calendar/", views.display_calendar_fbv, name="calendar"),
]
# --- END OF FILE urls.py ---
