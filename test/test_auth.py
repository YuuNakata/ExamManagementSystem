import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

# Helper to extract messages from response context
def get_message_texts(response):
    # Helper function to extract messages from the response context
    # Ensures that wsgi_request is available, which is needed for get_messages
    if hasattr(response, 'wsgi_request'):
        return [str(message) for message in get_messages(response.wsgi_request)]
    # Fallback for responses that might not have wsgi_request directly (e.g., after client.post without follow=True)
    # In such cases, messages are often in response.context if using TemplateResponse
    if response.context and 'messages' in response.context:
         return [str(message) for message in response.context['messages']]
    return []

@pytest.mark.django_db
class TestLogin:
    def test_login_success_student(self, client):
        """CU8-LOGIN-001: Ingreso exitoso con credenciales válidas de un Estudiante."""
        User = get_user_model()
        username = "estudiante_valido"
        email = "estudiante_valido@uci.cu" # Email provided in case needed, but login uses username
        password = "PasswordValido123"
        User.objects.create_user(username=username, email=email, password=password, role="estudiante")

        response = client.post(
            reverse("login"),
            {"username": username, "password": password},
            follow=False # Check redirect first
        )
        assert response.status_code == 302, "Should redirect on successful login"
        # Assuming LOGIN_REDIRECT_URL is 'dashboard'
        assert response.url == reverse("dashboard"), f"Should redirect to dashboard, got {response.url}"

        # Follow redirect and check if user is authenticated
        response_redirect = client.get(response.url, follow=True)
        assert response_redirect.status_code == 200, "Dashboard should be accessible"
        assert response_redirect.context['user'].is_authenticated, "User should be authenticated"
        assert response_redirect.context['user'].username == username, "Correct user should be logged in"

    def test_login_incorrect_password(self, client):
        """CU8-LOGIN-002: Ingreso fallido por contraseña incorrecta."""
        User = get_user_model()
        username = "estudiante_valido_pass"
        email = "estudiante_valido_pass@uci.cu"
        correct_password = "PasswordValido123"
        incorrect_password = "PasswordIncorrecto"
        User.objects.create_user(username=username, email=email, password=correct_password, role="estudiante")

        response = client.post(
            reverse("login"),
            {"username": username, "password": incorrect_password}
        )
        assert response.status_code == 200, "Should remain on login page"
        
        messages_from_context = get_message_texts(response)
        form = response.context.get('form')
        form_errors_str = str(form.non_field_errors()) if form and form.non_field_errors() else ""

        expected_message = "Por favor, introduzca un nombre de usuario y clave correctos. Observe que ambos campos pueden ser sensibles a mayúsculas."
        assert (expected_message in form_errors_str or
                "Usuario o contraseña incorrectos." in messages_from_context), \
            f"Expected error message not found. Messages: {messages_from_context}, Form Non-Field Errors: {form_errors_str}"
        assert not response.context['user'].is_authenticated, "User should not be authenticated"

    def test_login_non_existent_user(self, client):
        """CU8-LOGIN-003: Ingreso fallido por usuario inexistente."""
        response = client.post(
            reverse("login"),
            {"username": "usuario_inexistente", "password": "CualquierPassword"} # Using username, not email, for login
        )
        assert response.status_code == 200, "Should remain on login page"
        messages_from_context = get_message_texts(response)
        form = response.context.get('form')
        form_errors_str = str(form.non_field_errors()) if form and form.non_field_errors() else ""

        expected_message = "Por favor, introduzca un nombre de usuario y clave correctos. Observe que ambos campos pueden ser sensibles a mayúsculas."
        assert (expected_message in form_errors_str or
                "Usuario o contraseña incorrectos." in messages_from_context), \
            f"Expected error message not found. Messages: {messages_from_context}, Form Non-Field Errors: {form_errors_str}"
        assert not response.context['user'].is_authenticated, "User should not be authenticated"

    def test_login_empty_username(self, client):
        """CU8-LOGIN-004: Intento de ingreso con campo 'Usuario/Correo' vacío."""
        response = client.post(
            reverse("login"),
            {"username": "", "password": "PasswordValido123"}
        )
        assert response.status_code == 200, "Should remain on login page"
        form = response.context.get('form')
        assert form is not None, "Form should be in context"
        
        username_errors = form.errors.get('username', [])
        assert ("Este campo es obligatorio." in username_errors or 
                "Ingrese su nombre de usuario" in username_errors), \
            f"Expected username error not found. Form errors: {form.errors}"
        assert not response.context['user'].is_authenticated, "User should not be authenticated"

    def test_login_empty_password(self, client):
        """CU8-LOGIN-005: Intento de ingreso con campo 'Contraseña' vacío."""
        User = get_user_model()
        username = "estudiante_empty_pass"
        # Create user to ensure username is valid, only password is empty
        User.objects.create_user(username=username, password="PasswordValido123", role="estudiante")

        response = client.post(
            reverse("login"),
            {"username": username, "password": ""}
        )
        assert response.status_code == 200, "Should remain on login page"
        form = response.context.get('form')
        assert form is not None, "Form should be in context"

        password_errors = form.errors.get('password', [])
        assert ("Este campo es obligatorio." in password_errors or
                "Ingrese su contraseña" in password_errors), \
            f"Expected password error not found. Form errors: {form.errors}"
        assert not response.context['user'].is_authenticated, "User should not be authenticated"
