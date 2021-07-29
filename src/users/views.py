from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect

from .forms import StudentSignupForm, TeacherSignupForm, LoginForm


def signup_student(request):
    if request.method == "POST":
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False  # The user must be activated by the admin
            user.save()
            password = form.cleaned_data.get('password1')
            user = authenticate(username=user.email, password=password)
            login(request, user)
            return redirect("admin")
    else:
        form = StudentSignupForm()

    return render(request, "signup.html", {"form": form})


def signup_teacher(request):
    if request.method == "POST":
        form = TeacherSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False  # The user must be activated by the admin
            user.save()
            password = form.cleaned_data.get('password1')
            user = authenticate(username=user.email, password=password)
            login(request, user)
            return redirect("admin")
    else:
        form = TeacherSignupForm()

    return render(request, "signup.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("home")
    else:
        form = LoginForm()

    return render(request, "signup.html", {"form": form})
