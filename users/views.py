from django.shortcuts import redirect, render, get_object_or_404

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
            messages.success(request, f"Usuario {username} eliminado correctamente")
        except Exception as e:
            messages.error(request, f"Error al eliminar el usuario: {str(e)}")
        
        return redirect("users:user_management")
    
    return redirect("users:user_management")


@login_required
@admin_required
def update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        try:
            if form.is_valid():
                updated_user = form.save()
                messages.success(
                    request,
                    f"Usuario {updated_user.username} actualizado exitosamente.",
                )
                return redirect("users:user_management")
            else:
                # Si el formulario no es válido, captura los errores
                raise IntegrityError("Error en los datos del formulario.")

        except IntegrityError as e:
            # Maneja errores de base de datos (como campos nulos)
            messages.error(request, f"Error al actualizar: {str(e)}")
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
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            
            # Verificar si ya existe el usuario o el correo
            if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                messages.error(request, "Ya existe un usuario con este nombre/correo")
                
                if User.objects.filter(username=username).exists():
                    form.add_error('username', 'Nombre de usuario ya registrado')
                
                if User.objects.filter(email=email).exists():
                    form.add_error('email', 'Correo electrónico ya registrado')
                
                users = User.objects.all()
                return render(
                    request,
                    "user_management.html",
                    {
                        "users": users,
                        "register_form": form,
                        "register_modal_errors": True,
                    },
                )
            
            # Si no hay duplicados, crear el usuario
            user = form.save()
            messages.success(request, f"Usuario {user.username} creado exitosamente.")
            return redirect("users:user_management")
        
        # Si el formulario no es válido
        users = User.objects.all()
        return render(
            request,
            "user_management.html",
            {
                "users": users,
                "register_form": form,
                "register_modal_errors": True,
            },
        )
    
    # Si no es POST, redirigir al management
    return redirect("users:user_management")