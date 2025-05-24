import factory
from faker import Faker
from users.models import User

faker = Faker()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True  # Previene el problema de guardado en futuras versiones

    username = factory.Sequence(lambda n: f"user_{n}_{faker.user_name()}")  # Genera nombres únicos
    first_name = factory.LazyFunction(faker.first_name)
    last_name = factory.LazyFunction(faker.last_name)
    role = factory.LazyFunction(lambda: faker.random_element(["estudiante", "profesor", "admin"]))
    curso_programa = factory.LazyFunction(faker.sentence)
    departamento_facultad = factory.LazyFunction(faker.company)

    @factory.post_generation
    def set_user_password(obj, create, extracted, **kwargs):
        if extracted:
            obj.set_password(extracted)  # Usa la contraseña proporcionada
        else:
            obj.set_password("defaultpass")  # Usa una contraseña por defecto
        
        if create:
            obj.save()  # Guarda el usuario correctamente sin el problema de postgeneración
