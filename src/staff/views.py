from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied

from .forms import DepartmentAddForm
from users.models import Teacher, Student


def superuser(request):
    pass


def superuser_departments(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    t_dict = {"add_form": DepartmentAddForm()}
    return render(request, "staff_departments.html", t_dict)


def superuser_departments_add(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == "POST":
        form = DepartmentAddForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/superuser/departments")
        else:
            t_dict = {"add_form": form}
            return render(request, "staff_departments.html", t_dict)
    else:
        return redirect("/superuser/departments")


def superuser_users(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    max_rows = request.session.get("su_users_max_rows", 30)
    teachers_page = request.session.get("su_users_t_page", 1)
    students_page = request.session.get("su_users_s_page", 1)

    teachers = Teacher.objects.all()

    students = Student.objects.all()

    t_dict = {"students": students,
              "teachers": teachers}

    return render(request, "staff_users.html", t_dict)
