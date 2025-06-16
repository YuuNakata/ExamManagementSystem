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
    # Fetch unread notifications and evaluate the queryset immediately by converting to a list
    notifications_to_display = list(Notification.objects.filter(user=request.user, is_read=False).order_by('-timestamp'))

    # Now that we have the list of notifications to display, we can mark them as read in the DB.
    # The notification badge will update on the next request.
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    context = {
        'notifications': notifications_to_display,
        'page_title': 'Notificaciones' # Consistent page title
    }

    return render(request, "notifications.html", context)

def dashboard_view(request):
    context = get_calendar_data(request)
    if request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        context['unread_notifications'] = 0
    return render(request, "dashboard.html", context=context)
