from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path('', views.report_dashboard, name='report_dashboard'),
    path('generate/', views.generate_report, name='generate_report'),
    path('delete/', views.delete_last_report, name='delete_last_report'),
]
