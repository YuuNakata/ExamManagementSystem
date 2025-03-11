from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views, logout
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required


class CustomLoginView(auth_views.LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


class NotificationsView(TemplateView):
    template_name = "notifications.html"


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context
