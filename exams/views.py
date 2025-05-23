# --- START OF FILE views.py ---

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test # Added user_passes_test
from .forms import CalendarExamForm, GradeForm, ReviewRequestForm
from .models import CalendarExam, ExamRequest, ReviewRequest # Added ExamRequest
from datetime import date, timedelta, datetime # Added datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.urls import reverse # To build URLs for redirection
from django.views.decorators.http import require_POST


# Helper function to check if user is a student
def is_student(user):
    return hasattr(user, 'is_student') and user.is_student

# Helper function to check if user is a teacher
def is_teacher(user):
     # Adjust this based on your actual User model (e.g., user.is_teacher, user.role == 'teacher')
    return hasattr(user, 'is_teacher') and user.is_teacher


# ========= VISTAS DE CALENDARIO (EXISTENTES Y NUEVAS) =========

# Utility function (similar to get_calendar_context but more general)
def get_calendar_data(month_str=None, user=None):
    """
    Generates calendar data for a given month.

    Args:
        month_str (str, optional): Month string in 'YYYY-MM' format. Defaults to current month.
        user (User, optional): The logged-in user. Required for student view to check requests.

    Returns:
        dict: Context data including weeks, dates, exams, navigation months, etc.
    """
    try:
        # Use timezone.localdate() if using Django's timezone support
        current_date = (
            datetime.strptime(month_str, "%Y-%m").date()
            if month_str
            else timezone.localdate() # Use localdate for better timezone handling
        )
    except (ValueError, TypeError):
        current_date = timezone.localdate()

    first_day_of_month = current_date.replace(day=1)
    # Calculate the first day to display (could be from previous month)
    # weekday() returns 0 for Monday, 6 for Sunday
    start_day = first_day_of_month - timedelta(days=first_day_of_month.weekday())
    # Calculate the last day to display (ensure 6 weeks for consistency or calculate precisely)
    # A simple approach is to go forward enough days from start_day
    end_day = start_day + timedelta(days=6 * 7 - 1) # Display 6 weeks

    # Fetch exams within the *displayed* date range for efficiency
    exams_in_range = CalendarExam.objects.filter(
        date__gte=start_day, date__lte=end_day
    ).order_by("date", "turn")

    # Prepare exam data with status if user is provided (for student view)
    exams_data = []
    requested_exam_ids = set()
    if user and is_student(user):
        requested_exam_ids = set(ExamRequest.objects.filter(
            student=user,
            calendar_exam__in=exams_in_range
        ).values_list('calendar_exam_id', flat=True))

    today = timezone.localdate() # Use localdate
    for exam in exams_in_range:
        is_requested = exam.id in requested_exam_ids
        is_past = exam.date < today
        # Students can request if not past and not already requested
        can_request = is_student(user) and not is_past and not is_requested
        # Teachers can edit (or view if read_only is needed later)
        can_edit = is_teacher(user)

        exams_data.append({
            'instance': exam,
            'is_past': is_past,
            'is_requested_by_user': is_requested,
            'is_requestable': can_request,
            'is_editable': can_edit, # For potential future use or clarity
            # Add form only if needed (e.g., for teacher's edit view)
            'form': CalendarExamForm(instance=exam) if can_edit else None,
        })


    # Generate weeks structure
    weeks = []
    current_day = start_day
    while current_day <= end_day:
        week = []
        for i in range(7):
            day_info = {
                'date': current_day,
                'is_current_month': current_day.month == first_day_of_month.month,
                'is_today': current_day == today,
            }
            week.append(day_info)
            current_day += timedelta(days=1)
        weeks.append(week)


    # Navigation months
    prev_month_date = first_day_of_month - relativedelta(months=1)
    next_month_date = first_day_of_month + relativedelta(months=1)

    context = {
        "weeks": weeks,
        "current_month_date": first_day_of_month, # Represents the month being viewed
        "exams_data": exams_data,
        "prev_month": prev_month_date.strftime("%Y-%m"),
        "next_month": next_month_date.strftime("%Y-%m"),
        "modo_lectura": not is_teacher(user), # True for students, False for teachers
        # Add new_exam_form only for teachers
        "new_exam_form": CalendarExamForm(initial={'date': timezone.localdate().strftime('%Y-%m-%d')}) if is_teacher(user) else None,
         "error_in_modal_pk": None, # For handling form errors back in modal
         "error_in_new_modal": False,
    }
    return context


# STUDENT VIEW: Request Exam Calendar
@login_required
@user_passes_test(is_student, login_url='/login/') # Redirect if not a student
def request_exam(request):
    """
    Displays the calendar for students to view and request available exams.
    """
    month_str = request.GET.get("month")
    context = get_calendar_data(month_str=month_str, user=request.user)
    context['modo_lectura'] = True # Explicitly set read-only for students
    return render(request, "exams/request_exam.html", context)


# STUDENT ACTION: Submit Exam Request
@login_required
@user_passes_test(is_student, login_url='/login/')
def submit_exam_request(request):
    """
    Handles the POST request to create an ExamRequest.
    """
    if request.method != "POST":
        return redirect("exams:request_exam") # Or some error page

    calendar_exam_id = request.POST.get("calendar_exam_id")
    if not calendar_exam_id:
        messages.error(request, "No se especificó ningún examen.")
        return redirect("exams:request_exam") # Redirect back, maybe with month param

    try:
        exam = get_object_or_404(CalendarExam, pk=int(calendar_exam_id))
    except (ValueError, TypeError):
         messages.error(request, "ID de examen inválido.")
         return redirect("exams:request_exam")

    # --- Validation ---
    # 1. Check if exam is in the past
    if exam.is_past():
        messages.warning(request, f"No se puede solicitar el examen de '{exam.subject}' porque la fecha ya pasó.")
        # Redirect back to the month the user was viewing
        redirect_url = reverse('exams:request_exam') + f'?month={exam.date.strftime("%Y-%m")}'
        return redirect(redirect_url)

    # 2. Check if already requested by this student (database constraint also helps)
    already_requested = ExamRequest.objects.filter(student=request.user, calendar_exam=exam).exists()
    if already_requested:
        messages.info(request, f"Ya has solicitado el examen de '{exam.subject}'.")
        redirect_url = reverse('exams:request_exam') + f'?month={exam.date.strftime("%Y-%m")}'
        return redirect(redirect_url)

    # --- Create Request ---
    try:
        ExamRequest.objects.create(student=request.user, calendar_exam=exam)
        messages.success(request, f"Solicitud para el examen de '{exam.subject}' el {exam.date.strftime('%d/%m/%Y')} registrada correctamente.")
    except Exception as e: # Catch potential errors during creation (like unique constraint violation if check failed)
        messages.error(request, f"Ocurrió un error al registrar la solicitud: {e}")

    redirect_url = reverse('exams:request_exam') + f'?month={exam.date.strftime("%Y-%m")}'
    return redirect(redirect_url)


# TEACHER VIEW: Edit Calendar
@login_required
@user_passes_test(is_teacher, login_url='/login/') # Redirect if not a teacher
def edit_calendar(request):
    """
    Displays the calendar for teachers to manage exams (add/edit).
    Handles displaying validation errors back in modals.
    """
    month_str = request.GET.get("month")
    context = get_calendar_data(month_str=month_str, user=request.user)

    # Check if session contains info about failed form submissions
    error_modal_pk = request.session.pop('error_in_modal_pk', None)
    error_new_modal = request.session.pop('error_in_new_modal', False)
    failed_form_data = request.session.pop('failed_form_data', None)
    failed_form_errors = request.session.pop('failed_form_errors', None)

    if error_modal_pk and failed_form_data:
        # Re-populate the specific exam's form with errors
        for exam_data in context['exams_data']:
            if exam_data['instance'].pk == error_modal_pk:
                # Use data and errors to create a bound form instance
                exam_data['form'] = CalendarExamForm(failed_form_data, instance=exam_data['instance'])
                # Manually add errors if needed, though binding should handle it
                # exam_data['form']._errors = failed_form_errors # If needed
                break
        context['error_in_modal_pk'] = error_modal_pk # Signal template to open this modal
    elif error_new_modal and failed_form_data:
         # Re-populate the new exam form with errors
        context['new_exam_form'] = CalendarExamForm(failed_form_data)
        context['error_in_new_modal'] = True # Signal template to open this modal

    return render(request, "exams/calendar.html", context)


# TEACHER ACTION: Update Exam
@login_required
@user_passes_test(is_teacher, login_url='/login/')
def update_exam(request, pk):
    """
    Handles POST request to update an existing CalendarExam.
    Redirects back to edit_calendar, preserving month and opening modal on error.
    """
    exam = get_object_or_404(CalendarExam, pk=pk)
    month_param = exam.date.strftime("%Y-%m") # Get month for redirection
    redirect_url = reverse('exams:edit_calendar') + f'?month={month_param}'

    if request.method == "POST":
        form = CalendarExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, f"Examen de '{exam.subject}' actualizado correctamente.")
            return redirect(redirect_url)
        else:
            # Store error details in session to reopen modal
            request.session['error_in_modal_pk'] = pk
            request.session['failed_form_data'] = request.POST
            # request.session['failed_form_errors'] = form.errors.as_json() # Optional: pass specific errors
            messages.error(request, "Error al actualizar el examen. Por favor, corrige los campos.")
            return redirect(redirect_url) # Redirect back to edit view
    else:
        # Should not be accessed via GET directly usually, redirect away
        return redirect("exams:edit_calendar")


# TEACHER ACTION: Create Exam
@login_required
@user_passes_test(is_teacher, login_url='/login/')
def create_exam(request):
    """
    Handles POST request to create a new CalendarExam.
    Redirects back to edit_calendar, preserving month and opening modal on error.
    """
    if request.method == "POST":
        form = CalendarExamForm(request.POST)
        # Determine month for redirection *before* potential save
        date_str = request.POST.get('date')
        month_param = ""
        if date_str:
            try:
                exam_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                month_param = f"?month={exam_date.strftime('%Y-%m')}"
            except ValueError:
                 pass # Keep month_param empty, redirect to default month
        redirect_url = reverse('exams:edit_calendar') + month_param

        if form.is_valid():
            new_exam = form.save()
            messages.success(request, f"Nuevo examen de '{new_exam.subject}' creado correctamente.")
            return redirect(redirect_url)
        else:
             # Store error details in session to reopen modal
            request.session['error_in_new_modal'] = True
            request.session['failed_form_data'] = request.POST
            # request.session['failed_form_errors'] = form.errors.as_json() # Optional: pass specific errors
            messages.error(request, "Error al crear el examen. Por favor, corrige los campos.")
            return redirect(redirect_url) # Redirect back to edit view
    else:
         # Should not be accessed via GET directly, redirect away
        return redirect("exams:edit_calendar")

@login_required
@user_passes_test(is_teacher, login_url='/login/')
@require_POST # Es importante para seguridad
def delete_exam(request, pk):
    """
    Handles POST request to delete an existing CalendarExam.
    """
    exam = get_object_or_404(CalendarExam, pk=pk)
    exam_subject = exam.subject # Get details before deleting for message
    exam_date_str = exam.date.strftime('%d/%m/%Y')
    month_param = exam.date.strftime("%Y-%m") # For redirecting back to the correct month

    try:
        # Considerar añadir lógica aquí si un examen no se puede borrar
        # si ya tiene solicitudes de estudiantes asociadas, por ejemplo.
        exam.delete()
        messages.success(request, f"Examen de '{exam_subject}' del {exam_date_str} eliminado correctamente.")
    except Exception as e:
        # Podrías querer manejar el caso de ProtectedError si hay ExamRequests asociadas
        # from django.db.models import ProtectedError
        # if isinstance(e, ProtectedError):
        #    messages.error(request, f"No se puede eliminar el examen de '{exam_subject}' porque tiene solicitudes asociadas.")
        # else:
        messages.error(request, f"Ocurrió un error al eliminar el examen: {e}")
        # Log the error e for debugging purposes

    # Redirect back to the calendar view for the month the exam was in
    redirect_url = reverse('exams:edit_calendar') + f'?month={month_param}'
    return redirect(redirect_url)

# ========= VISTAS SIMPLES (MANTENIDAS/PLACEHOLDERS) =========
@login_required
def manage_grades(request):
    # Placeholder - Requires implementation
    return render(request, "exams/manage_grades.html")

@login_required
@user_passes_test(is_teacher, login_url='/login/')
def verify_requests(request):
    """
    Displays pending exam requests for teachers to approve or reject.
    """
    # Obtener solo las solicitudes pendientes, con datos relacionados del estudiante y examen
    pending_requests = ExamRequest.objects.filter(
        status='Pending'
    ).select_related(
        'student', 'calendar_exam'
    ).order_by('request_timestamp') # Ordenar por fecha de solicitud

    context = {
        'pending_requests': pending_requests,
    }
    return render(request, "exams/verify_requests.html", context)

@login_required
@user_passes_test(is_teacher, login_url='/login/')
@require_POST # Solo permitir POST para esta acción
def approve_request(request, pk):
    """
    Updates the status of an ExamRequest to 'Approved'.
    """
    # Obtenemos la solicitud, asegurándonos que existe y está pendiente
    request_obj = get_object_or_404(ExamRequest, pk=pk, status='Pending')

    try:
        request_obj.status = 'Approved'
        request_obj.save()
        messages.success(request, f"Solicitud de {request_obj.student.get_full_name()} para '{request_obj.calendar_exam.subject}' aprobada.")
    except Exception as e:
        messages.error(request, f"Error al aprobar la solicitud: {e}")
        # Considerar logging del error 'e'

    return redirect('exams:verify_requests')

@login_required
@user_passes_test(is_teacher, login_url='/login/')
@require_POST # Solo permitir POST para esta acción
def reject_request(request, pk):
    """
    Updates the status of an ExamRequest to 'Rejected'.
    """
     # Obtenemos la solicitud, asegurándonos que existe y está pendiente
    request_obj = get_object_or_404(ExamRequest, pk=pk, status='Pending')

    try:
        request_obj.status = 'Rejected'
        request_obj.save()
        messages.warning(request, f"Solicitud de {request_obj.student.get_full_name()} para '{request_obj.calendar_exam.subject}' rechazada.")
    except Exception as e:
        messages.error(request, f"Error al rechazar la solicitud: {e}")
         # Considerar logging del error 'e'

    return redirect('exams:verify_requests')

# This view might be redundant now if request_exam and edit_calendar cover all cases
# @login_required
# def calendar_view(request):
#     # Decide whether to show student or teacher view based on role
#     if is_teacher(request.user):
#         return redirect('exams:edit_calendar')
#     else:
#         return redirect('exams:request_exam')
# If you keep calendar_view, ensure its URL points here or remove the URL entry

@login_required
@user_passes_test(is_student, login_url='/login/')
def list_grades(request):
    """
    Muestra las calificaciones del estudiante logueado con detalles de revisiones.
    """
    # Obtener todos los exámenes calificados del estudiante
    graded_exams = ExamRequest.objects.filter(
        student=request.user,
        status='Approved',
        grade__isnull=False
    ).select_related('calendar_exam').order_by('-calendar_exam__date')

    # Obtener todas las revisiones relacionadas
    reviews = ReviewRequest.objects.filter(
        exam_request__student=request.user
    ).select_related('exam_request')

    context = {
        'graded_exams': graded_exams,
        'reviews': reviews,
    }
    return render(request, "exams/list_grades.html", context)

@login_required
@user_passes_test(is_teacher, login_url='/login/')
def manage_grades(request):
    """
    Vista para que los profesores asignen calificaciones a exámenes aprobados.
    """
    # Obtener exámenes aprobados sin calificar
    approved_requests = ExamRequest.objects.filter(
        status='Approved',
        grade__isnull=True
    ).select_related('student', 'calendar_exam')

    # Crear un formulario para cada solicitud
    grading_forms = []
    for exam_request in approved_requests:
        grading_forms.append({
            'exam_request': exam_request,
            'form': GradeForm(instance=exam_request)
        })

    context = {
        'grading_forms': grading_forms,
    }
    return render(request, "exams/manage_grades.html", context)


@login_required
@user_passes_test(is_student, login_url='/login/')
@require_POST
def submit_review_request(request):
    """
    Envía una solicitud de revisión para un examen calificado.
    """
    exam_request_id = request.POST.get('exam_request_id')
    exam_request = get_object_or_404(ExamRequest, pk=exam_request_id, student=request.user)
    
    form = ReviewRequestForm(request.POST)
    if form.is_valid():
        ReviewRequest.objects.create(
            exam_request=exam_request,
            reason=form.cleaned_data['reason'],
            status='Pending'
        )
        messages.success(request, "Solicitud de revisión enviada.")
    else:
        messages.error(request, "Error al enviar. Completa el motivo.")
    
    return redirect('exams:request_review')
@login_required
@user_passes_test(is_student, login_url='/login/')
def request_review(request):
    """
    Vista para que estudiantes soliciten revisión de exámenes calificados.
    """
    # Obtener exámenes calificados del estudiante
    graded_exams = ExamRequest.objects.filter(
        student=request.user,
        status='Approved',
        grade__isnull=False
    ).exclude(review_requests__status='Pending') 

    # Obtener revisiones pendientes del estudiante
    pending_reviews = ReviewRequest.objects.filter( 
        exam_request__student=request.user,
        status='Pending'
    ).select_related('exam_request')

    context = {
        'graded_exams': graded_exams,
        'pending_reviews': pending_reviews,
        'review_form': ReviewRequestForm(),
    }
    return render(request, "exams/request_review.html", context)

# --- END OF FILE views.py ---