from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.http import Http404

from users.forms import SigninForm

from .models import Department
from .forms import DepartmentAddForm


# ====================================================================
# Helpers
# ====================================================================

def init_render_dict(request):
    t_dict = {
        "user": {
            "is_superuser": request.user.is_superuser,
            "is_authenticated": request.user.is_authenticated
        }
    }

    if not request.user.is_authenticated:
        t_dict["user"]["signin_form"] = SigninForm()

    return t_dict


# ====================================================================
# /
# ====================================================================

def home(request):
    return redirect("departments")


# ====================================================================
# /departments
# ====================================================================

def departments(request):
    t_dict = init_render_dict(request)
    t_dict["departments"] = Department.objects.all()

    return render(request, "departments.html", t_dict)


# ====================================================================
# /departments/insert
# ====================================================================

def departments_insert(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == "POST":
        return departments_insert_post(request)

    return departments_insert_get(request)


def departments_insert_get(request, form=False):
    t_dict = {
        "form": form if form else DepartmentAddForm(),
        "t": {
            "title": "Insert department",
            "sumbit_value": "Insert"
        }
    }

    return render(request, "base_form.html", t_dict)


def departments_insert_post(request):
    form = DepartmentAddForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect("departments")
    else:
        return departments_insert_get(request, form=form)


# ====================================================================
# /departments/<int:dept_id>/update
# ====================================================================

def departments_update(request, dept_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    try:
        dept_obj = Department.objects.get(id=dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    if request.method == "POST":
        return departments_update_post(request, dept_id, dept_obj)

    return departments_update_get(request, dept_id, dept_obj)


def departments_update_get(request, dept_id, dept_obj, form=False):
    t_dict = {
        "form": form if form else DepartmentAddForm(instance=dept_obj),
        "t": {
            "title": "Update department",
            "sumbit_value": "Update"
        }
    }

    return render(request, "base_form.html", t_dict)


def departments_update_post(request, dept_id, dept_obj):
    form = DepartmentAddForm(request.POST, instance=dept_obj)
    if form.is_valid():
        form.save()
        return redirect("departments")
    else:
        return departments_update_get(request, dept_id, dept_obj, form=form)


# ====================================================================
# /departments/<int:dept_id>/delete
# ====================================================================

def departments_delete(request, dept_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    try:
        dept_obj = Department.objects.get(id=dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    if request.method == "POST":
        dept_obj.delete()
        return redirect("departments")

    t_dict = {
        "t": {
            "title": f"Delete {dept_obj.name}",
            "confirm_text": ("Are you sure that you want to delete the"
                             f" department {dept_obj.name}?"),
            "return_url": "/departments"
        }
    }

    return render(request, "confirm_form.html", t_dict)
