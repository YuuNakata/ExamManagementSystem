from django.shortcuts import redirect, render, get_object_or_404

from exam_management.decorators import admin_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import User
from users.forms import UserRegisterForm, UserUpdateForm
from django.contrib import messages


@login_required
@admin_required
def user_management(request):
    search_query = request.GET.get("q", "")

    if search_query:
        users = User.objects.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )
    else:
        users = User.objects.all()
    register_form = UserRegisterForm()
    for user in users:
        user.update_form = UserUpdateForm(instance=user)

    return render(
        request,
        "user_management.html",
        {"users": users, "search_query": search_query, "register_form": register_form},
    )


@login_required
@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.delete()
        messages.success(request, f"Usuario {user.username} eliminado correctamente")
        return redirect("users:user_management")
    return redirect("users:user_management")


@login_required
@admin_required
def update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save()
            messages.success(
                request, f"Usuario {updated_user.username} actualizado exitosamente."
            )
            return redirect("users:user_management")

        # Si hay errores, recargar la página principal con los errores
        users = User.objects.all()
        register_form = UserRegisterForm()
        return render(
            request,
            "user_management.html",
            {
                "users": users,
                "register_form": register_form,
                "edit_modal_errors": form.errors,
                "editing_user_id": user_id,
            },
        )


@login_required
@admin_required
def register_user(request):
    print(request)
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario {user.username} creado exitosamente.")
            return redirect("users:user_management")
        users = User.objects.all()
        return render(
            request,
            "user_management.html",
            {
                "users": users,
                "register_form": form,
                "register_modal_errors": form.errors,
            },
        )
