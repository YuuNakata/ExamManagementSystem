from django.urls import path
from .views import request_exam, confirmation

app_name = "exams"

urlpatterns = [
    path("solicitar/", request_exam, name="request_exam"),
    path("confirmacion/", confirmation, name="confirmation"),
]
