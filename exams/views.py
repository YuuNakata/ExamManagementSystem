from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ExamRequestForm, CalendarExamForm
from .models import CalendarExam
from datetime import date, timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta


# ========= VISTAS EXISTENTES (MANTENIDAS) =========
@login_required
def request_exam(request):
    if request.method == "POST":
        form = ExamRequestForm(request.POST)
        if form.is_valid():
            exam_request = form.save(commit=False)
            exam_request.student = request.user
            exam_request.save()
            return redirect("exams:confirmation")
        messages.error(request, "Error en los datos. Revise los campos.")
    else:
        form = ExamRequestForm()
    return render(request, "exams/request_exam.html", {"form": form})


@login_required
def confirmation(request):
    return render(request, "exams/confirmation.html")


# ========= VISTAS DE CALENDARIO (ACTUALIZADAS) =========
@login_required
def edit_calendar(request):
    context = get_calendar_context(request, False)
    return render(request, "exams/calendar.html", context)


@login_required
def update_exam(request, pk):
    exam = get_object_or_404(CalendarExam, pk=pk)

    if not request.user.is_teacher:
        return redirect("exams:edit_calendar")

    if request.method == "POST":
        form = CalendarExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            return redirect("exams:edit_calendar")
        else:
            # Eliminar el examen si el formulario es inválido
            exam.delete()
            messages.error(request, "Examen eliminado por datos inválidos")
            return redirect("exams:edit_calendar")

    else:
        form = CalendarExamForm(instance=exam)

    return render(request, "exams/calendar.html", {"form": form})


@login_required
def create_exam(request):

    initial_data = {}
    date_param = request.GET.get("date")

    if date_param:
        try:
            initial_data["date"] = timezone.datetime.strptime(
                date_param, "%Y-%m-%d"
            ).date()
        except:
            pass

    if request.method == "POST":
        form = CalendarExamForm(request.POST)
        if form.is_valid():
            new_exam = form.save(commit=False)
            new_exam.save()
        return redirect("exams:edit_calendar")
    else:
        form = CalendarExamForm(initial=initial_data)

    return render(request, "exams/calendar.html", {"form": form})


def get_calendar_context(request, read_only=True):
    # Obtener mes actual
    month = request.GET.get("month")
    try:
        current_date = (
            timezone.datetime.strptime(month, "%Y-%m").date()
            if month
            else timezone.now().date()
        )
    except:
        current_date = timezone.now().date()

    first_day = current_date.replace(day=1)
    last_day = first_day + relativedelta(months=1) - timedelta(days=1)

    # Crear lista de días del mes
    weeks = []
    current_day = first_day
    while current_day <= last_day:
        week = []
        for _ in range(7):
            week.append(current_day)
            current_day += timedelta(days=1)
            if current_day.month != first_day.month:
                break
        weeks.append(week)

    exams = CalendarExam.objects.filter(
        date__month=first_day.month, date__year=first_day.year
    ).order_by("date", "turn")

    context = {
        "weeks": weeks,
        "current_month": first_day,
        "exams": exams,
        "modo_lectura": read_only,
    }
    if not read_only:
        prev_month = (first_day - timedelta(days=1)).strftime("%Y-%m")
        next_month = (first_day + relativedelta(months=1)).strftime("%Y-%m")

        context["prev_month"] = prev_month
        context["next_month"] = next_month
        for exam in exams:
            exam.form = CalendarExamForm(instance=exam)
        context["exams"] = exams
        context["new_exam_form"] = CalendarExamForm(
            initial={"date": current_date.strftime("%Y-%m-%d")}
        )

    return context


# ========= VISTAS SIMPLES (MANTENIDAS) =========
@login_required
def manage_grades(request):
    return render(request, "exams/manage_grades.html")


@login_required
def verify_requests(request):
    return render(request, "exams/verify_requests.html")


@login_required
def calendar_view(request):
    return render(request, "exams/calendar.html")


@login_required
def list_grades(request):
    return render(request, "exams/list_grades.html")


@login_required
def request_review(request):
    return render(request, "exams/request_review.html")
