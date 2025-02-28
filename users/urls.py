from django.urls import path
from .views import register_user, user_management, update_user, delete_user

app_name = "users"

urlpatterns = [
    path("register/", register_user, name="register"),
    path("manage/", user_management, name="user_management"),
    path("update/<int:user_id>/", update_user, name="update_user"),
    path("delete/<int:user_id>/", delete_user, name="delete_user"),
]
