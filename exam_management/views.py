from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views, logout
from django.contrib.auth.decorators import login_required
from exams.views import get_calendar_data
from django.http import JsonResponse
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
    return render(request, "notifications.html", context=get_calendar_data(request))

@login_required
def notifications_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"count": count})

@login_required
def notifications_list(request):
    notes = Notification.objects.filter(user=request.user) \
                                .order_by('-timestamp')[:10]
    data = [{
        "id":        n.id,
        "message":   n.message,
        "timestamp": n.timestamp.strftime("%Y-%m-%d %H:%M"),
        "is_read":   n.is_read,
    } for n in notes]
    return JsonResponse({"notifications": data})

@login_required
def mark_notification_read(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    return JsonResponse({"success": True})

def dashboard_view(request):
    return render(request, "dashboard.html", context=get_calendar_data(request))

def notificar(user, message):
    Notification.objects.create(user=user, message=message)
