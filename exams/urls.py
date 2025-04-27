# --- START OF FILE urls.py ---

from django.urls import path
from . import views

app_name = "exams"

urlpatterns = [
    # Student URLs
    path("request-exam/", views.request_exam, name="request_exam"),
    path("submit-request/", views.submit_exam_request, name="submit_exam_request"), # New URL for submitting request
    path("list-grades/", views.list_grades, name="list_grades"),
    path("request-review/", views.request_review, name="request_review"),

    # Teacher URLs
    path("edit-calendar/", views.edit_calendar, name="edit_calendar"), # Teacher's calendar view
    path("edit-exam/<int:pk>/", views.update_exam, name="edit_exam"),   # Action URL for updating
    path("create-exam/", views.create_exam, name="create_exam"),
    path("delete-exam/<int:pk>/", views.delete_exam, name="delete_exam"),
    path("manage-grades/", views.manage_grades, name="manage_grades"),
    path("verify-requests/", views.verify_requests, name="verify_requests"), # Vista principal
    path("approve-request/<int:pk>/", views.approve_request, name="approve_request"), # Acción Aprobar
    path("reject-request/<int:pk>/", views.reject_request, name="reject_request"),   # Acción Rechazar

    # Generic Calendar URL - remove or make it redirect based on role if needed
    # path("calendar/", views.calendar_view, name="calendar"), # This might be confusing, consider removing
]
# --- END OF FILE urls.py ---