from django.urls import path
from .views import GenerateReportsView

app_name = "reports"

urlpatterns = [
    path("generate/", GenerateReportsView.as_view(), name="generate"),
]
