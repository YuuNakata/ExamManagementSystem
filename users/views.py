from django.shortcuts import redirect, render

from exam_management.decorators import admin_required
from django.contrib.auth.decorators import login_required

from users.forms import UserRegisterForm
from django.contrib import messages


@login_required
@admin_required
def register_user(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario {user.username} creado exitosamente.")
            return redirect("dashboard")
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})
