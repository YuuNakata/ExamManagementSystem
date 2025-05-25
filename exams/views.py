# --- START OF FILE views.py ---

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)  
from django.db.models import Q
from datetime import date, timedelta, datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.urls import reverse_lazy, reverse 
from django.views.decorators.http import require_POST
from users.models import User
from .forms import CalendarExamForm, GradeForm, ReviewRequestForm
from .models import CalendarExam, ExamRequest, ReviewRequest  
from exam_management.models import Notification
from exam_management.utils import notificar

# Helper function to check if user is a student
def is_student(user):
    return hasattr(user, "is_student") and user.is_student


# Helper function to check if user is a teacher
def is_teacher(user):
    return hasattr(user, "is_teacher") and user.is_teacher


# ========= VISTAS DE CALENDARIO (EXISTENTES Y NUEVAS) =========


# Utility function (similar to get_calendar_context but more general)
def get_calendar_data(month_str=None, user=None):
    try:
        current_date = (
            datetime.strptime(month_str, "%Y-%m").date()
            if month_str
            else timezone.localdate()  
        )
    except (ValueError, TypeError):
        current_date = timezone.localdate()

    first_day_of_month = current_date.replace(day=1)
    start_day = first_day_of_month - timedelta(days=first_day_of_month.weekday())
    end_day = start_day + timedelta(days=6 * 7 - 1)  

    exams_in_range = CalendarExam.objects.filter(
        date__gte=start_day, date__lte=end_day
    ).order_by("date", "turn")

    exams_data = []
    requested_exam_ids = set()
    if user and is_student(user):
        requested_exam_ids = set(
            ExamRequest.objects.filter(
                student=user, calendar_exam__in=exams_in_range
            ).values_list("calendar_exam_id", flat=True)
        )

    today = timezone.localdate()  
    for exam in exams_in_range:
        is_requested = exam.id in requested_exam_ids
        is_past = exam.date < today
        can_request = is_student(user) and not is_past and not is_requested
        can_edit = is_teacher(user)

        exams_data.append(
            {
                "instance": exam,
                "is_past": is_past,
                "is_requested_by_user": is_requested,
                "is_requestable": can_request,
                "is_editable": can_edit,  
                "form": CalendarExamForm(instance=exam) if can_edit else None,
            }
        )

    weeks = []
    current_day = start_day
    while current_day <= end_day:
        week = []
        for i in range(7):
            day_info = {
                "date": current_day,
                "is_current_month": current_day.month == first_day_of_month.month,
                "is_today": current_day == today,
            }
            week.append(day_info)
            current_day += timedelta(days=1)
        weeks.append(week)

    prev_month_date = first_day_of_month - relativedelta(months=1)
    next_month_date = first_day_of_month + relativedelta(months=1)

    context = {
        "weeks": weeks,
        "current_month_date": first_day_of_month,  
        "exams_data": exams_data,
        "prev_month": prev_month_date.strftime("%Y-%m"),
        "next_month": next_month_date.strftime("%Y-%m"),
        "modo_lectura": not is_teacher(user),  
        "new_exam_form": (
            CalendarExamForm(
                initial={"date": timezone.localdate().strftime("%Y-%m-%d")}
            )
            if is_teacher(user)
            else None
        ),
        "error_in_modal_pk": None,  
        "error_in_new_modal": False,
    }
    return context


# STUDENT VIEW: Request Exam Calendar
@login_required
@user_passes_test(is_student, login_url="/login/")  
def request_exam(request):
    month_str = request.GET.get("month")
    context = get_calendar_data(month_str=month_str, user=request.user)
    context["modo_lectura"] = True  
    return render(request, "exams/request_exam.html", context)


# STUDENT ACTION: Submit Exam Request
@login_required
@user_passes_test(is_student, login_url="/login/")
def submit_exam_request(request):
    if request.method != "POST":
        return redirect("exams:request_exam")  

    calendar_exam_id = request.POST.get("calendar_exam_id")
    if not calendar_exam_id:
        messages.error(request, "No se especificó ningún examen.")
        return redirect("exams:request_exam")  

    try:
        exam = get_object_or_404(CalendarExam, pk=int(calendar_exam_id))
    except (ValueError, TypeError):
        messages.error(request, "ID de examen inválido.")
        return redirect("exams:request_exam")

    if exam.is_past():
        messages.warning(
            request,
            f"No se puede solicitar el examen de '{exam.subject}' porque la fecha ya pasó.",
        )
        redirect_url = (
            reverse("exams:request_exam") + f'?month={exam.date.strftime("%Y-%m")}'
        )
        return redirect(redirect_url)

    already_requested = ExamRequest.objects.filter(
        student=request.user, calendar_exam=exam
    ).exists()
    if already_requested:
        messages.info(request, f"Ya has solicitado el examen de '{exam.subject}'.")
        redirect_url = (
            reverse("exams:request_exam") + f'?month={exam.date.strftime("%Y-%m")}'
        )
        return redirect(redirect_url)

    try:
        ExamRequest.objects.create(student=request.user, calendar_exam=exam)
        messages.success(
            request,
            f"Solicitud para el examen de '{exam.subject}' el {exam.date.strftime('%d/%m/%Y')} registrada correctamente.",
        )
    except Exception as e:
        messages.error(request, f"Ocurrió un error al registrar la solicitud: {e}")

    redirect_url = (
        reverse("exams:request_exam") + f'?month={exam.date.strftime("%Y-%m")}'
    )
    return redirect(redirect_url)


# TEACHER VIEW: Edit Calendar
@login_required
@user_passes_test(is_teacher, login_url="/login/")  
def edit_calendar(request):
    month_str = request.GET.get("month")
    context = get_calendar_data(month_str=month_str, user=request.user)

    error_modal_pk = request.session.pop("error_in_modal_pk", None)
    error_new_modal = request.session.pop("error_in_new_modal", False)
    failed_form_data = request.session.pop("failed_form_data", None)
    failed_form_errors = request.session.pop("failed_form_errors", None)

    if error_modal_pk and failed_form_data:
        for exam_data in context["exams_data"]:
            if exam_data["instance"].pk == error_modal_pk:
                exam_data["form"] = CalendarExamForm(
                    failed_form_data, instance=exam_data["instance"]
                )
                break
        context["error_in_modal_pk"] = error_modal_pk  
    elif error_new_modal and failed_form_data:
        context["new_exam_form"] = CalendarExamForm(failed_form_data)
        context["error_in_new_modal"] = True  

    return render(request, "exams/calendar.html", context)


# TEACHER ACTION: Update Exam
@login_required
@user_passes_test(is_teacher, login_url="/login/")
def update_exam(request, pk):
    exam = get_object_or_404(CalendarExam, pk=pk)
    month_param = exam.date.strftime("%Y-%m")  
    redirect_url = reverse("exams:edit_calendar") + f"?month={month_param}"

    if request.method == "POST":
        form = CalendarExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Examen de '{exam.subject}' actualizado correctamente."
            )
            return redirect(redirect_url)
        else:
            request.session["error_in_modal_pk"] = pk
            request.session["failed_form_data"] = request.POST
            messages.error(
                request, "Error al actualizar el examen. Por favor, corrige los campos."
            )
            return redirect(redirect_url)  
    else:
        return redirect("exams:edit_calendar")


# TEACHER ACTION: Create Exam
@login_required
@user_passes_test(is_teacher, login_url="/login/")
def create_exam(request):
    if request.method == "POST":
        form = CalendarExamForm(request.POST)
        date_str = request.POST.get("date")
        month_param = ""
        if date_str:
            try:
                exam_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                month_param = f"?month={exam_date.strftime('%Y-%m')}"
            except ValueError:
                pass  
        redirect_url = reverse("exams:edit_calendar") + month_param

        if form.is_valid():
            new_exam = form.save()
            messages.success(
                request, f"Nuevo examen de '{new_exam.subject}' creado correctamente."
            )
            return redirect(redirect_url)
        else:
            request.session["error_in_new_modal"] = True
            request.session["failed_form_data"] = request.POST
            messages.error(
                request, "Error al crear el examen. Por favor, corrige los campos."
            )
            return redirect(redirect_url)  
    else:
        return redirect("exams:edit_calendar")


@login_required
@user_passes_test(is_teacher, login_url="/login/")
@require_POST  
def delete_exam(request, pk):
    exam = get_object_or_404(CalendarExam, pk=pk)
    exam_subject = exam.subject  
    exam_date_str = exam.date.strftime("%d/%m/%Y")
    month_param = exam.date.strftime("%Y-%m")  

    try:
        exam.delete()
        messages.success(
            request,
            f"Examen de '{exam_subject}' del {exam_date_str} eliminado correctamente.",
        )
    except Exception as e:
        messages.error(request, f"Ocurrió un error al eliminar el examen: {e}")

    redirect_url = reverse("exams:edit_calendar") + f"?month={month_param}"
    return redirect(redirect_url)


# ========= VISTAS SIMPLES (MANTENIDAS/PLACEHOLDERS) =========

# Mixins are removed as decorators will be used for FBVs.
# class ProfessorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
#     def test_func(self):
#         return is_teacher(self.request.user)
# 
#     def handle_no_permission(self):
#         messages.error(self.request, "Acceso denegado. Solo para profesores.")
#         return redirect("login") 
# 
# 
# class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
#     def test_func(self):
#         return is_student(self.request.user)
# 
#     def handle_no_permission(self):
#         messages.error(self.request, "Acceso denegado. Solo para estudiantes.")
#         return redirect("login")


# Was: class VerifyRequestsView(LoginRequiredMixin, ProfessorRequiredMixin, ListView):
@login_required
@user_passes_test(is_teacher, login_url="/login/")
def verify_requests_fbv(request):
    """Displays pending exam requests for professors to review."""
    pending_requests = (
        ExamRequest.objects.filter(status="Pending")
        .select_related("student", "calendar_exam")
        .order_by("calendar_exam__date", "student__last_name")
    )
    context = {
        "pending_requests": pending_requests,  # Changed key here
        "page_title": "Verificar Solicitudes de Examen",
    }
    return render(request, "exams/verify_requests.html", context)


# Was: class ManageGradesListView(LoginRequiredMixin, ProfessorRequiredMixin, ListView):
@login_required
@user_passes_test(is_teacher, login_url="/login/")
def manage_grades_list_fbv(request):
    """Displays approved exam requests for professors to grade."""
    exam_requests_query = (
        ExamRequest.objects.filter(status="Approved")
        .select_related("student", "calendar_exam")
        .order_by("-calendar_exam__date", "calendar_exam__subject")
    )

    subject_query = request.GET.get('subject_query')
    student_query = request.GET.get('student_query')
    date_filter = request.GET.get('date_filter')

    if subject_query:
        exam_requests_query = exam_requests_query.filter(calendar_exam__subject__icontains=subject_query)
    
    if student_query:
        exam_requests_query = exam_requests_query.filter(
            Q(student__username__icontains=student_query) |
            Q(student__first_name__icontains=student_query) |
            Q(student__last_name__icontains=student_query)
        )

    if date_filter:
        try:
            # Ensure date_filter is a valid date before filtering
            parsed_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            exam_requests_query = exam_requests_query.filter(calendar_exam__date=parsed_date)
        except ValueError:
            # Handle invalid date format, perhaps log it or message the user
            messages.warning(request, "Formato de fecha inválido. Use YYYY-MM-DD.")
            # Optionally, don't filter by date or return an empty set if strict

    grade_form = GradeForm()

    context = {
        "exam_requests": exam_requests_query,
        "page_title": "Gestionar Calificaciones",
        "grade_form": grade_form,
    }
    return render(request, "exams/manage_grades.html", context)


# Was: class GradeExamRequestView(LoginRequiredMixin, ProfessorRequiredMixin, UpdateView):
@login_required
@user_passes_test(is_teacher, login_url="/login/")
def grade_exam_request_fbv(request, pk):
    """Allows professors to assign a grade to an approved exam request."""
    exam_request = get_object_or_404(ExamRequest, pk=pk)

    if exam_request.status != "Approved":
        messages.error(request, "Solo se pueden calificar solicitudes aprobadas.")
        return redirect("exams:manage_grades_list")

    if request.method == "POST":
        form = GradeForm(request.POST, instance=exam_request)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Calificación para {exam_request.student.get_full_name()} en {exam_request.calendar_exam.subject} guardada exitosamente.",
            )
            # Create notification for student
            Notification.objects.create(
                user=exam_request.student,
                message=f"Tu calificación para {exam_request.calendar_exam.subject} ha sido registrada/actualizada."
            )
            return redirect("exams:manage_grades")
        else:
            # Form is invalid, re-render manage_grades.html with errors and necessary context
            messages.error(request, "Error al guardar la calificación. Por favor, corrige los errores.")
            
            # Re-fetch the base context for manage_grades.html
            exam_requests_to_grade = (
                ExamRequest.objects.filter(status="Approved")
                .select_related("student", "calendar_exam")
                .order_by("-calendar_exam__date", "calendar_exam__subject")
            )
            # This is the generic, unbound form for other modals if needed, or if user closes error modal
            unbound_grade_form = GradeForm() 

            context = {
                "exam_requests": exam_requests_to_grade,
                "page_title": "Gestionar Calificaciones",
                "grade_form": unbound_grade_form, # The generic form for new modal openings
                "grade_form_with_errors": form, # The submitted form with errors
                "exam_request_id_with_error": pk, # ID to re-open the correct modal
            }
            return render(request, "exams/manage_grades.html", context)
    else:
        # This GET case should ideally not be hit if all grading is via modal on manage_grades page.
        # If it is, it means a direct navigation to /grade-exam/PK/ which is not the modal flow.
        # For now, redirect to manage_grades, as the modal should handle form display.
        # Alternatively, one could pre-populate the form for a non-modal GET, but that's not the current goal.
        # messages.info(request, "Para asignar calificaciones, por favor usa la lista de 'Gestionar Calificaciones'.")
        return redirect("exams:manage_grades") # Or render a simple page saying to use the modal


@login_required
@user_passes_test(is_student, login_url="/login/")
def list_my_grades_fbv(request):
    """Displays graded exams for the logged-in student."""
    graded_exams_query = (
        ExamRequest.objects.filter(student=request.user, status="Approved", grade__isnull=False)
        .select_related("calendar_exam")
        .order_by("-calendar_exam__date")
    )

    subject_query = request.GET.get('subject_query')
    if subject_query:
        graded_exams_query = graded_exams_query.filter(calendar_exam__subject__icontains=subject_query)

    context = {
        "graded_exams": graded_exams_query,
        "page_title": "Mis Calificaciones",
    }
    return render(request, "exams/list_grades.html", context)


# Was: class CalendarView(LoginRequiredMixin, ListView):
@login_required
def display_calendar_fbv(request):
    """Displays the general exam calendar, adapting to user role (student/teacher)."""
    month_str = request.GET.get("month")
    error_in_modal_pk = request.session.pop("error_in_modal_pk", None)
    error_in_new_modal = request.session.pop("error_in_new_modal", False)

    context = get_calendar_data(month_str=month_str, user=request.user)
    context["error_in_modal_pk"] = error_in_modal_pk
    context["error_in_new_modal"] = error_in_new_modal

    return render(request, "exams/calendar.html", context)


@login_required
@user_passes_test(is_teacher, login_url="/login/")
@require_POST
def approve_request_fbv(request, pk):
    """Approves an exam request."""
    exam_request = get_object_or_404(ExamRequest, pk=pk)
    if exam_request.status == "Pending":
        exam_request.status = "Approved"
        exam_request.save()
        # Notificar al estudiante
        notificar(
            exam_request.student,
            f"Tu solicitud para el examen '{exam_request.calendar_exam.subject}' fue APROBADA."
        )
        messages.success(
            request,
            f"Solicitud de {exam_request.student.get_full_name()} para {exam_request.calendar_exam} aprobada.",
        )
    else:
        messages.warning(request, "La solicitud ya no estaba pendiente.")
    return redirect("exams:verify_requests")


@login_required
@user_passes_test(is_teacher, login_url="/login/")
@require_POST
def reject_request_fbv(request, pk):
    """Rejects an exam request."""
    exam_request = get_object_or_404(ExamRequest, pk=pk)
    if exam_request.status == "Pending":
        exam_request.status = "Rejected"
        exam_request.save()
        # Notificar al estudiante
        notificar(
            exam_request.student,
            f"Tu solicitud para el examen '{exam_request.calendar_exam.subject}' fue RECHAZADA."
        )
        messages.warning(
            request,
            f"Solicitud de {exam_request.student.get_full_name()} para {exam_request.calendar_exam} rechazada.",
        )
    else:
        messages.warning(request, "La solicitud ya no estaba pendiente.")
    return redirect("exams:verify_requests")


@login_required
@user_passes_test(is_student, login_url="/login/")
@require_POST
def submit_review_request(request):
    exam_request_id = request.POST.get("exam_request_id")
    exam_request = get_object_or_404(
        ExamRequest, pk=exam_request_id, student=request.user
    )

    form = ReviewRequestForm(request.POST)
    if form.is_valid():
        review = ReviewRequest.objects.create(
            exam_request=exam_request,
            reason=form.cleaned_data['reason'],
            status='Pending'
        )
        # Notificar a los profesores (o solo al responsable si lo tienes)
        professors = User.objects.filter(role="profesor")
        for prof in professors:
            notificar(
                prof,
                f"El estudiante {request.user.get_full_name()} ha solicitado una revisión para el examen '{exam_request.calendar_exam.subject}'."
            )
        messages.success(request, "Solicitud de revisión enviada.")
    else:
        messages.error(request, "Error al enviar. Completa el motivo.")

    return redirect("exams:request_review")


@login_required
@user_passes_test(is_student, login_url="/login/")
def request_review(request):
    graded_exams = ExamRequest.objects.filter(
        student=request.user, status="Approved", grade__isnull=False
    ).exclude(review_requests__status="Pending")

    pending_reviews = ReviewRequest.objects.filter(
        exam_request__student=request.user, status="Pending"
    ).select_related("exam_request")

    context = {
        "graded_exams": graded_exams,
        "pending_reviews": pending_reviews,
        "review_form": ReviewRequestForm(),
    }
    return render(request, "exams/request_review.html", context)


# --- END OF FILE views.py ---
