from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ExamRequestForm


@login_required
def request_exam(request):
    if request.method == "POST":
        form = ExamRequestForm(request.POST)
        if form.is_valid():
            exam_request = form.save(commit=False)
            exam_request.student = request.user
            exam_request.save()
            return redirect("exams:confirmation")
        else:
            messages.error(request, "Error en los datos. Revise los campos.")
    else:
        form = ExamRequestForm()

    return render(request, "exams/request_exam.html", {"form": form})


@login_required
def confirmation(request):
    return render(request, "exams/confirmation.html")
