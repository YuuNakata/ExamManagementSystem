from django.test import TestCase
from django.contrib.auth.models import User

class LoginTestCase(TestCase):
    def setUp(self):
        """Crear un usuario de prueba"""
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_login_exitoso(self):
        """Probar autenticación exitosa"""
        response = self.client.post("/login/", {"username": "testuser", "password": "testpass"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bienvenido")

    def test_login_fallido(self):
        """Probar login con contraseña incorrecta"""
        response = self.client.post("/login/", {"username": "testuser", "password": "wrongpass"})
        self.assertEqual(response.status_code, 401)
        self.assertContains(response, "Credenciales incorrectas")
