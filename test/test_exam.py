from django.test import TestCase
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from exams.models import CalendarExam, ExamRequest
from datetime import date, timedelta
from django.contrib.messages import get_messages
from exams.views import is_student # For diagnostic check

# Helper to extract messages from response context
def get_message_texts(response):
    return [m.message for m in list(response.context.get('messages', []))]

@pytest.mark.django_db
def test_view_calendar_current_month(client):
    """CU5-VISCAL-001: Usuario visualiza el calendario del mes actual."""
    User = get_user_model()
    user = User.objects.create_user(username="testuser_cal_current", password="testpass", role="student")
    client.force_login(user)
    url_request_exam = reverse("exams:request_exam")
    response = client.get(url_request_exam) # No follow=True
    assert response.status_code == 302
    assert response.url.startswith(f"/login/?next={url_request_exam}")


@pytest.mark.django_db
def test_view_calendar_different_month(client):
    """CU5-VISCAL-002: Usuario navega a un mes diferente en el calendario."""
    User = get_user_model()
    user = User.objects.create_user(username="testuser_cal_diff", password="testpass", role="student")
    client.force_login(user)
    url_request_exam = reverse("exams:request_exam")
    response = client.get(url_request_exam, {"month": "6", "year": "2025"}) # No follow=True
    assert response.status_code == 302
    assert response.url.startswith(f"/login/?next={url_request_exam}")


@pytest.mark.django_db
def test_view_calendar_empty_month(client):
    """CU5-VISCAL-003: Usuario visualiza un calendario sin exámenes publicados para ese mes."""
    User = get_user_model()
    user = User.objects.create_user(username="testuser_cal_empty", password="testpass", role="student")
    client.force_login(user)
    url_request_exam = reverse("exams:request_exam")
    response = client.get(url_request_exam, {"month": "12", "year": "2025"}) # No follow=True
    assert response.status_code == 302
    assert response.url.startswith(f"/login/?next={url_request_exam}")


@pytest.mark.django_db
def test_add_exam_to_calendar(client):
    """CU10-EDITCAL-001: Profesor agrega un nuevo examen al calendario."""
    User = get_user_model()
    user = User.objects.create_user(username="profesor_adds_exam", password="testpass", role="profesor")
    client.force_login(user)
    response = client.post(
        reverse("exams:create_exam"),
        {
            "date": "2025-04-10",
            "turn": "1",
            "exam_type": "suficiencia",
            "subject": "Database",
        },
        follow=True  
    )
    assert response.status_code == 200 
    messages = get_message_texts(response)
    assert "Nuevo examen de 'Database' creado correctamente." in messages


@pytest.mark.django_db
def test_add_exam_without_subject(client):
    """CU10-EDITCAL-003: Profesor intenta agregar examen sin seleccionar asignatura."""
    User = get_user_model()
    user = User.objects.create_user(username="profesor_add_no_subject", password="testpass", role="profesor")
    client.force_login(user)
    response = client.post(
        reverse("exams:create_exam"),
        {"date": "2025-04-12", "turn": "1", "exam_type": "premio", "subject": ""}, 
        follow=True
    )
    assert response.status_code == 200
    messages = get_message_texts(response)
    assert "Error al crear el examen. Por favor, corrige los campos." in messages
    assert "El campo 'Asignatura' no puede estar vacío." in response.context['form'].non_field_errors()


@pytest.mark.django_db
def test_accept_exam_request(client):
    """CU4-VERSOL-001: Profesor acepta una solicitud de examen pendiente."""
    User = get_user_model()
    professor = User.objects.create_user(username="profesor_accepts", password="testpass", role="profesor")
    client.force_login(professor)

    # Create a student user with a name for the message
    student = User.objects.create_user(username="student_requests", password="testpass", role="student", first_name="Test", last_name="Student")

    calendar_exam = CalendarExam.objects.create(
        date="2025-07-15",
        turn="1",
        exam_type="suficiencia",
        subject="Test Subject for Acceptance"
    )

    exam_request = ExamRequest.objects.create(
        student=student,
        calendar_exam=calendar_exam,
        status='Pending'
    )

    response = client.post(
        reverse("exams:approve_request", kwargs={"pk": exam_request.id}), # Correct URL
        # No data needed as pk is in URL and it's a direct action
        follow=True
    )
    assert response.status_code == 200
    messages = get_message_texts(response)
    expected_message = f"Solicitud de {student.get_full_name()} para '{calendar_exam.subject}' aprobada."
    assert expected_message in messages


@pytest.mark.django_db
def test_request_sufficiency_exam(client):
    """CU3-SOLEX-001: Estudiante solicita un examen de Suficiencia."""
    User = get_user_model()
    # Use 'estudiante' as the role value, matching the User.is_student property
    student = User.objects.create_user(username="estudiante_sufficiency", password="testpass", role="estudiante")
    client.force_login(student)

    # The is_student check should now pass with the correct role
    assert is_student(student) == True, "is_student(student) should be True with role='estudiante'"

    future_date = date.today() + timedelta(days=10)
    calendar_exam = CalendarExam.objects.create(
        date=future_date,
        turn="1",
        exam_type="suficiencia",
        subject="Programación Web para Suficiencia"
    )

    response = client.post(
        reverse("exams:submit_exam_request"),
        {"calendar_exam_id": calendar_exam.id},
        follow=False # Check initial redirect first
    )
    assert response.status_code == 302 # Should redirect after successful POST
    # submit_exam_request redirects to request_exam, possibly with month param
    expected_redirect_start = reverse("exams:request_exam")
    assert response.url.startswith(expected_redirect_start), \
        f"Expected redirect to start with {expected_redirect_start}, got {response.url}"

    # Now follow the redirect and check for the message
    response_get = client.get(response.url, follow=True)
    assert response_get.status_code == 200
    messages_get = get_message_texts(response_get)
    expected_message_get = f"Solicitud para el examen de '{calendar_exam.subject}' el {future_date.strftime('%d/%m/%Y')} registrada correctamente."
    assert expected_message_get in messages_get


@pytest.mark.django_db
def test_create_exam_without_type(client):
    """Test: Profesor intenta crear un examen sin seleccionar tipo de examen."""
    User = get_user_model()
    professor = User.objects.create_user(username="profesor_no_type", password="testpass", role="profesor")
    client.force_login(professor)

    future_date = date.today() + timedelta(days=10)
    response = client.post(
        reverse("exams:create_exam"),
        {
            "date": future_date.strftime("%Y-%m-%d"),
            "turn": "1",
            "exam_type": "",
            "subject": "Incomplete Subject"
        },
        follow=True
    )
    assert response.status_code == 200
    messages = get_message_texts(response)
    assert "Error al crear el examen. Por favor, corrige los campos." in messages
    assert "El campo 'Tipo de examen' no puede estar vacío." in response.context['form'].non_field_errors()
