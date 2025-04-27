from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views, logout
from django.contrib.auth.decorators import login_required
from exams.views import get_calendar_data


class CustomLoginView(auth_views.LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def notifications_view(request):
    return render(request, "notifications.html", context=get_calendar_data(request))


def dashboard_view(request):
    return render(request, "dashboard.html", context=get_calendar_data(request))
