from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse

from exam_management.decorators import admin_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import User
from users.forms import UserRegisterForm, UserUpdateForm
from django.contrib import messages
from django.db import IntegrityError


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
    
    # Verificar si el usuario intenta eliminarse a sí mismo
    if request.user.id == user.id:
        messages.error(request, "No puedes eliminarte a ti mismo")
        return redirect("users:user_management")
    
    if request.method == "POST":
        try:
            username = user.username
            user.delete()
            messages.success(request, "Eliminación completada")
        except Exception as e:
            messages.error(request, f"Error al eliminar el usuario: {str(e)}")
        
        return redirect("users:user_management")
    
    return redirect("users:user_management")


@login_required
@admin_required
def update_user(request, user_id):
    user_to_update = get_object_or_404(User, id=user_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user_to_update)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Usuario {user_to_update.username} actualizado exitosamente.",
            )
            if is_ajax:
                return JsonResponse({'status': 'success'})
            return redirect("users:user_management")
        else:
            if is_ajax:
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            else:
                # Fallback for non-AJAX
                users = User.objects.all()
                register_form = UserRegisterForm()
                for user in users:
                    if user.id == user_to_update.id:
                        user.update_form = form
                    else:
                        user.update_form = UserUpdateForm(instance=user)

                return render(
                    request,
                    "user_management.html",
                    {
                        "users": users,
                        "register_form": register_form,
                        "editing_user_id": user_id,
                    },
                )


@login_required
@admin_required
def register_user(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Usuario registrado exitosamente.")
            if is_ajax:
                return JsonResponse({'status': 'success'})
            return redirect("users:user_management")
        else: # Form is invalid
            if is_ajax:
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            
            # Fallback for non-AJAX
            users = User.objects.all()
            for u in users:
                u.update_form = UserUpdateForm(instance=u)
            return render(
                request,
                "user_management.html",
                {
                    "users": users,
                    "register_form": form,
                    "register_modal_errors": True,
                },
            )
    
    return redirect("users:user_management")