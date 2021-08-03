from django.contrib.auth import login, logout
from django.shortcuts import render, redirect

from .forms import StudentSignupForm, TeacherSignupForm, SigninForm


def signup_student(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = StudentSignupForm(request.POST)
        t_dict = {"signin_form": SigninForm(),
                  "teacher_form": TeacherSignupForm(),
                  "student_form": form}
        if form.is_valid():
            form.save()
            t_dict["user_created"] = True
            t_dict["user_first_name"] = form.cleaned_data.get("first_name")
            t_dict["student_form"] = StudentSignupForm()

        return render(request, "signup.html", t_dict)
    else:
        return redirect("signup")


def signup_teacher(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = TeacherSignupForm(request.POST)
        t_dict = {"signin_form": SigninForm(),
                  "teacher_form": form,
                  "student_form": StudentSignupForm()}
        if form.is_valid():
            form.save()
            t_dict["user_created"] = True
            t_dict["user_first_name"] = form.cleaned_data.get("first_name")
            t_dict["teacher_form"] = TeacherSignupForm()

        return render(request, "signup.html", t_dict)
    else:
        return redirect("signup")


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

    t_dict = {
        "signin_form": SigninForm(),
        "teacher_form": TeacherSignupForm(),
        "student_form": StudentSignupForm()
    }

    return render(request, "signup.html", t_dict)


def signin(request):
    if request.method == "POST":
        form = SigninForm(request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("home")
    else:
        form = SigninForm()

    return render(request, "mainpage.html", {"signin_form": form})


def signout(request):
    logout(request)
    return redirect("home")
