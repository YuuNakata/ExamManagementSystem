from django.shortcuts import render
from django.views.generic import TemplateView


class GenerateReportsView(TemplateView):
    template_name = "reports/generate.html"
