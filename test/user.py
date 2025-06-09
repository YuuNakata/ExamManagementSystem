import pytest
from users.factories import UserFactory
from users.models import User

@pytest.mark.django_db
def test_bulk_user_creation():
    UserFactory.create_batch(25)  # Crear 500 usuarios
    assert User.objects.count() >= 25  # Comprobar que existen en la BD

