from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied

from .forms import DepartmentAddForm


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
