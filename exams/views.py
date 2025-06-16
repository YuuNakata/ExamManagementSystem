# --- START OF FILE views.py ---

from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)  
from users.models import User
from exam_management.models import Notification
from django.db.models import F, Q
from exam_management.utils import notificar
from datetime import date, timedelta, datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.urls import reverse_lazy, reverse 
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.template.loader import render_to_string
from users.models import User
from .forms import CalendarExamForm, GradeForm, ReviewRequestForm
from .models import CalendarExam, ExamRequest, ReviewRequest  
from exam_management.models import Notification
from django.db import IntegrityError
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
        exam_id_int = int(calendar_exam_id)
        exam = get_object_or_404(CalendarExam, pk=exam_id_int)
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
        professors = User.objects.filter(role="profesor")
        for prof in professors:
            notificar(
                prof,
                f"El estudiante {request.user.get_full_name()} ha solicitado inscribirse en el examen '{exam.subject}'."
            )
    except Exception as e:
        messages.error(request, f"Ocurrió un error al registrar la solicitud: {e}")

    final_redirect_url = (
        reverse("exams:request_exam") + f'?month={exam.date.strftime("%Y-%m")}'
    )
    return redirect(final_redirect_url)


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
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == "POST":
        form = CalendarExamForm(request.POST, instance=exam)
        if form.is_valid():
            # Additional validation for duplicates
            exam_type = form.cleaned_data['exam_type']
            subject = form.cleaned_data['subject']
            date = form.cleaned_data['date']
            
            first_day_of_month = date.replace(day=1)
            last_day_of_month = (first_day_of_month + relativedelta(months=1)) - timedelta(days=1)
            
            existing_exam = CalendarExam.objects.filter(
                exam_type=exam_type,
                subject=subject,
                date__range=[first_day_of_month, last_day_of_month]
            ).exclude(pk=pk).exists()
            
            if existing_exam:
                form.add_error(None, f"Ya existe un examen de tipo '{exam_type}' para la asignatura '{subject}' en este mes.")
            else:
                form.save()
                
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': 'Examen actualizado con éxito.'})
                messages.success(request, "Examen actualizado con éxito.")
                month_param = f"?month={date.strftime('%Y-%m')}"
                return redirect(reverse("exams:edit_calendar") + month_param)

        # If form is invalid (including the custom duplicate error)
        if is_ajax:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        
        request.session["error_in_modal_pk"] = pk
        request.session["failed_form_data"] = request.POST
        messages.error(request, "Por favor, corrige los errores en el formulario.")
        month_param = f"?month={exam.date.strftime('%Y-%m')}"
        return redirect(reverse("exams:edit_calendar") + month_param)

    return redirect("exams:edit_calendar")


# TEACHER ACTION: Create Exam
@login_required
@user_passes_test(is_teacher, login_url="/login/")
def create_exam(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == "POST":
        form = CalendarExamForm(request.POST)
        if form.is_valid():
            exam_type = form.cleaned_data['exam_type']
            subject = form.cleaned_data['subject']
            date = form.cleaned_data['date']
            
            first_day_of_month = date.replace(day=1)
            last_day_of_month = (first_day_of_month + relativedelta(months=1)) - timedelta(days=1)
            
            existing_exam = CalendarExam.objects.filter(
                exam_type=exam_type,
                subject=subject,
                date__range=[first_day_of_month, last_day_of_month]
            ).exists()
            
            if existing_exam:
                form.add_error(None, f"Ya existe un examen de tipo '{exam_type}' para la asignatura '{subject}' en este mes.")
            else:
                new_exam = form.save()
                students = User.objects.filter(role="estudiante")
                for student in students:
                    notificar(student, f"Se ha creado un nuevo examen de '{new_exam.subject}' el {new_exam.date.strftime('%d/%m/%Y')}.")
                messages.success(request, f"Nuevo examen de '{new_exam.subject}' creado correctamente.")
                if is_ajax:
                    month_param = f"?month={date.strftime('%Y-%m')}"
                    redirect_url = reverse("exams:edit_calendar") + month_param
                    return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
                return redirect(reverse("exams:edit_calendar"))

        # If form is invalid (including the custom duplicate error)
        if is_ajax:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        
        # Fallback for non-AJAX
        date_str = request.POST.get("date")
        month_param = ""
        if date_str:
            try:
                exam_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                month_param = f"?month={exam_date.strftime('%Y-%m')}"
            except ValueError:
                pass
        redirect_url = reverse("exams:edit_calendar") + month_param
        request.session["error_in_new_modal"] = True
        request.session["failed_form_data"] = request.POST
        messages.error(request, "Por favor, corrige los campos.")
        return redirect(redirect_url)

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
            "Examen eliminado.",
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
# exams/views.py
@login_required
@user_passes_test(is_teacher, login_url="/login/")
def verify_requests_fbv(request):
    # Obtener TODAS las solicitudes pendientes sin filtrar por asignatura
    exam_requests = ExamRequest.objects.filter(
        status="Pending"
    ).select_related('student', 'calendar_exam')

    review_requests = ReviewRequest.objects.filter(
        status="Pending"
    ).select_related('exam_request__student', 'exam_request__calendar_exam')

    context = {
        'exam_requests': exam_requests,
        'review_requests': review_requests,
        'page_title': 'Verificar Solicitudes'
    }
    return render(request, 'exams/verify_requests.html', context)


# Was: class ManageGradesListView(LoginRequiredMixin, ProfessorRequiredMixin, ListView):
@login_required
@user_passes_test(is_teacher, login_url="/login/")
def manage_grades_list_fbv(request):
    """Displays approved exam requests for professors to grade."""
    exam_requests_query = (
        ExamRequest.objects.filter(status="Approved")
        .select_related("student", "calendar_exam")
        .order_by(F("grade").asc(nulls_first=True), "-calendar_exam__date")
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
    """Asigna o actualiza calificación de un examen"""
    exam_request = get_object_or_404(
        ExamRequest.objects.select_related('student', 'calendar_exam'),
        pk=pk,
        status='Approved'
    )

    if request.method == "POST":
        # Obtener el valor directamente del POST (ignorando el form.cleaned_data temporalmente)
        raw_new_grade = request.POST.get('grade')
        
        try:
            # Convertir a float con exactamente 1 decimal
            new_grade = float(raw_new_grade)
            current_grade = float(exam_request.grade) if exam_request.grade is not None else None
            
            # Comparación numérica exacta
            if current_grade is not None and abs(new_grade - current_grade) < 0.05:  # Tolerancia mínima para floats
                messages.warning(request,
                    f"La calificación ingresada es igual a la actual.")
                exam_requests = ExamRequest.objects.filter(status='Approved').order_by('-calendar_exam__date')
                return render(request, 'exams/manage_grades.html', {
                    'exam_requests': exam_requests,
                    'grade_form': GradeForm(request.POST),
                    'exam_request_id_with_error': pk
                })
            
            # Si son diferentes, proceder con el guardado
            exam_request.grade = round(new_grade, 1)  # Redondear a 1 decimal
            exam_request.save()

            student_name = exam_request.student.get_full_name() or exam_request.student.username
            subject_name = exam_request.calendar_exam.subject

            if current_grade is None:
                success_message = f"Éxito Calificación para {student_name} en {subject_name} guardada exitosamente"
                notification_message = f"Calificación asignada en {subject_name}: {new_grade}"
            else:
                success_message = f"Calificación actualizada: {current_grade} -> {new_grade}"
                notification_message = f"Calificación actualizada en {subject_name}: {new_grade}"

            messages.success(request, success_message)
            
            Notification.objects.create(
                user=exam_request.student,
                message=notification_message
            )
            
            return redirect('exams:manage_grades')
            
        except (TypeError, ValueError):
            messages.error(request, "Formato de calificación inválido")
    
    # Manejo de GET o errores
    exam_requests = ExamRequest.objects.filter(status='Approved').order_by('-calendar_exam__date')
    return render(request, 'exams/manage_grades.html', {
        'exam_requests': exam_requests,
        'grade_form': GradeForm(instance=exam_request),
        'exam_request_id_with_error': None
    })


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

    # Get IDs of exam requests that already have a review
    reviews_requested_ids = set(
        ReviewRequest.objects.filter(exam_request__student=request.user).values_list(
            "exam_request_id", flat=True
        )
    )

    context = {
        "graded_exams": graded_exams_query,
        "reviews_requested_ids": reviews_requested_ids,
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

# BLOQUE DE REVISION ---------------JAVIER
# exams/views.py
@login_required
@user_passes_test(is_student, login_url="/login/")
@require_POST
def submit_review_request(request):
    exam_request_id = request.POST.get("exam_request")
    reason = request.POST.get("reason", "").strip()

    if not reason:
        messages.error(request, "El motivo de la revisión no puede estar vacío.")
        return redirect("exams:request_review")

    try:
        exam_request = ExamRequest.objects.get(
            pk=int(exam_request_id),
            student=request.user,
            status="Approved",
            grade__isnull=False
        )

        # Prevent duplicate review requests
        if ReviewRequest.objects.filter(exam_request=exam_request).exists():
            messages.error(request, "Ya existe una solicitud de revisión para esta calificación.")
            return redirect("exams:request_review")

        # Create and save the new review request
        review = ReviewRequest(exam_request=exam_request, reason=reason)
        review.full_clean()
        review.save()

        # Notify all teachers, using the working pattern from submit_exam_request
        professors = User.objects.filter(role="profesor")
        student_name = request.user.get_full_name() or request.user.username
        subject_name = exam_request.calendar_exam.subject

        for prof in professors:
            notificar(
                prof,
                f"El estudiante {student_name} ha solicitado una revisión para el examen de {subject_name}."
            )

        messages.success(request, "Solicitud de revisión creada exitosamente.")
        return redirect("exams:request_review")

    except (ValidationError, ExamRequest.DoesNotExist) as e:
        if isinstance(e, ValidationError):
            messages.error(request, "Error de validación. Asegúrese de que el motivo sea válido.")
        else:
            messages.error(request, "No se pudo encontrar la solicitud de examen especificada.")
        return redirect("exams:request_review")
    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado: {str(e)}")
        return redirect("exams:request_review")

# exams/views.py
@login_required
@user_passes_test(is_student)
def request_review(request):
    # Get IDs of exam requests that already have any review request
    existing_review_ids = ReviewRequest.objects.filter(
        exam_request__student=request.user
    ).values_list('exam_request_id', flat=True)

    # Get graded exams for the student that do NOT have a review request yet
    graded_exams = ExamRequest.objects.filter(
        student=request.user,
        status='Approved',
        grade__isnull=False
    ).exclude(id__in=existing_review_ids)

    # Get pending reviews to show their status on the same page
    pending_reviews = ReviewRequest.objects.filter(
        exam_request__student=request.user,
        status='Pending'
    )

    context = {
        'graded_exams': graded_exams,
        'pending_reviews': pending_reviews
    }
    return render(request, 'exams/request_review.html', context)

@login_required
@user_passes_test(is_teacher)
def verify_requests_fbv(request):
    # Obtener todas las solicitudes pendientes
    exam_requests = ExamRequest.objects.filter(status='Pending')
    review_requests = ReviewRequest.objects.filter(status='Pending')
    
    context = {
        'exam_requests': exam_requests,
        'review_requests': review_requests
    }
    return render(request, 'exams/verify_requests.html', context)

@login_required
@user_passes_test(is_teacher, login_url="/login/")
def approve_review(request, pk):
    review = get_object_or_404(ReviewRequest, pk=pk)
    
    if request.method == "POST":
        new_grade = request.POST.get("new_grade")
        
        # Conversión segura para comparación
        try:
            current_grade = str(float(review.exam_request.grade))  # Normalizamos a float y luego a string
            new_grade_compare = str(float(new_grade))  # Convertimos el input a float y luego a string
        except (ValueError, TypeError):
            messages.error(request, "Formato de calificación inválido")
            return redirect("exams:verify_requests")
        
        # Verificación precisa de igualdad
        if current_grade == new_grade_compare:
            messages.warning(request, "La calificación ingresada es igual a la actual.")
            context = {'review': review}
            return render(request, 'exams/adjust_grade.html', context)
        
        try:
            # Actualización de la calificación
            review.exam_request.grade = float(new_grade)  # Guardamos como float
            review.exam_request.save()
            
            review.status = "Approved"
            review.save()
            
            Notification.objects.create(
                user=review.exam_request.student,
                message=f"Revisión aprobada en {review.exam_request.calendar_exam.subject}. Nueva calificación: {new_grade}"
            )
            
            messages.success(request, "Revisión aprobada y calificación actualizada")
        except Exception as e:
            messages.error(request, f"Error al actualizar: {str(e)}")
        
        return redirect("exams:verify_requests")
    
    context = {'review': review}
    return render(request, 'exams/adjust_grade.html', context)

@login_required
@user_passes_test(is_teacher, login_url="/login/")
@require_POST
def reject_review(request, pk):
    review = get_object_or_404(ReviewRequest, pk=pk)
    review.status = "Rejected"
    review.save()
    
    # Notificar estudiante
    Notification.objects.create(
        user=review.exam_request.student,
        message=f"Revisión rechazada en {review.exam_request.calendar_exam.subject}"
    )
    

    return redirect("exams:verify_requests")

# --- END OF FILE views.py ---
