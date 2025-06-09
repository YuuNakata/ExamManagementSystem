import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from django.contrib.messages import get_messages
import re

# Prueba 1: Prevención de auto-eliminación de administradores
@pytest.mark.django_db
def test_admin_self_deletion_prevention():
    admin = User.objects.create_superuser(
        username='admin', 
        email='admin@example.com',
        password='password',
        is_staff=True
    )
    client = Client()
    client.force_login(admin)
    
    response = client.post(reverse('users:delete_user', args=[admin.id]))
    
    # Verificar que el usuario no fue eliminado
    assert User.objects.filter(id=admin.id).exists()
    
    # Verificar mensaje de error
    messages = list(get_messages(response.wsgi_request))
    assert any("No puedes eliminar tu propia cuenta" in str(message) for message in messages)

# Prueba 2: XSS en mensajes flash
@pytest.mark.django_db
def test_xss_vulnerability_in_messages():
    admin = User.objects.create_superuser(
        username='admin', 
        email='admin@example.com',
        password='password',
        is_staff=True
    )
    malicious_user = User.objects.create_user(
        username="<script>alert('hacked')</script>",
        email='xss@example.com',
        password='password'
    )
    client = Client()
    client.force_login(admin)
    
    # Intentar eliminar usuario con nombre malicioso
    response = client.post(reverse('users:delete_user', args=[malicious_user.id]))
    
    # Verificar que el script no se ejecuta
    messages = list(get_messages(response.wsgi_request))
    message_content = str(messages[0])
    assert '<script>' not in message_content
    assert '&lt;script&gt;' in message_content  # Debería estar escapado

# Prueba 3: Inyección SQL en búsqueda
@pytest.mark.django_db
def test_sql_injection_in_search():
    admin = User.objects.create_superuser(
        username='admin', 
        email='admin@example.com',
        password='password',
        is_staff=True
    )
    client = Client()
    client.force_login(admin)
    
    # Payload de inyección SQL
    malicious_payload = "' OR 1=1; --"
    
    response = client.get(
        reverse('users:user_management') + f"?q={malicious_payload}"
    )
    
    # Verificar que no hay errores del sistema
    assert response.status_code == 200
    assert "error" not in response.content.decode().lower()
    
    # Verificar que no se muestran todos los usuarios
    assert "Total de usuarios: 1" in response.content.decode()

# Prueba 4: Exposición de información sensible en errores
@pytest.mark.django_db
def test_sensitive_data_exposure():
    admin = User.objects.create_superuser(
        username='admin', 
        email='admin@example.com',
        password='password',
        is_staff=True
    )
    client = Client()
    client.force_login(admin)
    
    # Intentar actualizar con datos inválidos (provocar IntegrityError)
    response = client.post(
        reverse('users:update_user', args=[admin.id]),
        {'email': '', 'username': 'newadmin'}  # Email vacío provocará error
    )
    
    # Verificar que no se muestran detalles internos
    messages = list(get_messages(response.wsgi_request))
    assert any("Error de integridad" in str(message) for message in messages)
    assert "violates not-null constraint" not in str(messages[0])

# Prueba 5: IDOR (Insecure Direct Object Reference)
@pytest.mark.django_db
def test_idor_vulnerability():
    # Crear dos usuarios regulares
    user1 = User.objects.create_user(
        username='user1',
        email='user1@example.com',
        password='password'
    )
    user2 = User.objects.create_user(
        username='user2',
        email='user2@example.com',
        password='password'
    )
    client = Client()
    client.force_login(user1)
    
    # User1 intenta eliminar a User2
    response = client.post(reverse('users:delete_user', args=[user2.id]))
    
    # Verificar acceso denegado
    assert response.status_code == 403
    assert User.objects.filter(id=user2.id).exists()

# Prueba 6: CSRF protection
@pytest.mark.django_db
def test_csrf_protection():
    admin = User.objects.create_superuser(
        username='admin', 
        email='admin@example.com',
        password='password',
        is_staff=True
    )
    victim = User.objects.create_user(
        username='victim',
        email='victim@example.com',
        password='password'
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(admin)
    
    # Obtener token CSRF válido
    client.get(reverse('users:user_management'))
    csrf_token = client.cookies['csrftoken'].value
    
    # Simular ataque CSRF con token inválido
    response = client.post(
        reverse('users:delete_user', args=[victim.id]),
        {},
        HTTP_X_CSRFTOKEN='invalid_token'
    )
    
    # Verificar que la acción no se realizó
    assert response.status_code == 403
    assert User.objects.filter(id=victim.id).exists()

# Prueba 7: Validación de entrada en búsqueda
@pytest.mark.django_db
def test_search_input_validation():
    admin = User.objects.create_superuser(
        username='admin', 
        email='admin@example.com',
        password='password',
        is_staff=True
    )
    client = Client()
    client.force_login(admin)
    
    # Entrada maliciosa con caracteres peligrosos
    malicious_input = "'; DROP TABLE users; --"
    
    response = client.get(
        reverse('users:user_management') + f"?q={malicious_input}"
    )
    
    # Verificar que no hay errores del sistema
    assert response.status_code == 200
    assert "error" not in response.content.decode().lower()
    
    # Verificar que la entrada fue saneada
    assert "DROP TABLE" not in response.content.decode()