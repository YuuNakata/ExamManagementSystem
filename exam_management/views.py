from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views, logout
from django.contrib.auth.decorators import login_required
from exams.views import get_calendar_data
from exam_management.models import Notification

class CustomLoginView(auth_views.LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def notifications_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    context = get_calendar_data(request)
    context['notifications'] = Notification.objects.filter(user=request.user).order_by('-timestamp')[:20]
    context['unread_notifications'] = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "notifications.html", context=context)

def dashboard_view(request):
    context = get_calendar_data(request)
    if request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        context['unread_notifications'] = 0
    return render(request, "dashboard.html", context=context)
