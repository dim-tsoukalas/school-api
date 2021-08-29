from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.db.models import Max

from users.models import Deptadmin, Teacher
from users.forms import SigninForm

from classes.models import Classes, Teaching

from .models import Department, DepartmentTeachers, DepartmentStudents
from .forms import DepartmentAddForm, DepartmentStateForm


# ====================================================================
# Helpers
# ====================================================================

def init_render_dict(request):
    d = {
        "user": {
            "object": request.user,
            "is_superuser": request.user.is_superuser,
            "is_authenticated": request.user.is_authenticated
        },
        "university": {
            "name": "Example University"
        }
    }

    if request.user.is_authenticated:
        d["user"].update({
            "id": request.user.id,
            "is_teacher": request.user.is_teacher,
            "is_student": request.user.is_student,
            "is_deptadmin": request.user.is_deptadmin
        })
        if request.user.is_teacher:
            d["user"].update({
                "teacher": {
                    "departments": DepartmentTeachers.objects.filter(
                        user_id=request.user
                    )
                }
            })
        elif request.user.is_student:
            d["user"].update({
                "student": {
                    "departments": DepartmentStudents.objects.filter(
                        user_id=request.user
                    )
                }
            })
        elif request.user.is_deptadmin:
            d["user"].update({
                "deptadmin": {
                    "department": Deptadmin.objects.get(
                        user=request.user
                    ).department
                }
            })
    else:
        d["user"]["signin_form"] = SigninForm()

    return d


def render_dict_add_perm(d, request, dept_id, class_public_id=False):
    user = request.user

    is_admin = False
    is_teacher = False

    if user.is_authenticated:
        if user.is_superuser:
            is_admin = True
        elif user.is_deptadmin:
            if Deptadmin.objects.get(user=user).department.id == dept_id:
                is_admin = True
        elif class_public_id and user.is_teacher:
            try:
                year = Teaching.objects.aggregate(Max("year"))["year__max"]
                class_obj = Classes.objects.get(public_id=class_public_id)
                teacher = Teacher.objects.get(user=user)
                Teaching.objects.get(
                    class_id=class_obj, teacher=teacher, year=year)
                is_teacher = True
            except (Classes.DoesNotExist, Teacher.DoesNotExist,
                    Teaching.DoesNotExist):
                pass

    d.update({
        "perm": {
            "is_admin": is_admin,
            "is_teacher": is_teacher
        }
    })
    return d


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
    d = init_render_dict(request)
    d["base_form"] = {
        "form": form if form else DepartmentAddForm(),
        "title": "Insert department",
        "submit_value": "Insert"
    }
    return render(request, "base_form.html", d)


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
    d = init_render_dict(request)
    d = render_dict_add_perm(d, request, dept_id)

    if not d["perm"]["is_admin"]:
        raise PermissionDenied

    try:
        dept_obj = Department.objects.get(id=dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    if request.method == "POST":
        return departments_update_post(request, d, dept_obj)

    return departments_update_get(request, d, dept_obj)


def departments_update_get(request, d, dept_obj, form=False):
    d["base_form"] = {
        "form": form if form else DepartmentAddForm(instance=dept_obj),
        "title": "Update department",
        "submit_value": "Update"
    }
    return render(request, "base_form.html", d)


def departments_update_post(request, d, dept_obj):
    form = DepartmentAddForm(request.POST, instance=dept_obj)
    if form.is_valid():
        form.save()
        return redirect("departments")
    else:
        return departments_update_get(request, d, dept_obj, form=form)


# ====================================================================
# /departments/<int:dept_id>/state
# ====================================================================

def departments_state(request, dept_id):
    d = init_render_dict(request)
    d = render_dict_add_perm(d, request, dept_id)

    if not d["perm"]["is_admin"]:
        raise PermissionDenied

    try:
        dept_obj = Department.objects.get(id=dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    if request.method == "POST":
        return departments_state_post(request, d, dept_obj)

    return departments_state_get(request, d, dept_obj)


def departments_state_get(request, d, dept_obj, form=False):
    d["base_form"] = {
        "form": form if form else DepartmentStateForm(
            dept_obj, instance=dept_obj),
        "title": "Update department state",
        "submit_value": "Save"
    }
    return render(request, "base_form.html", d)


def departments_state_post(request, d, dept_obj):
    form = DepartmentStateForm(dept_obj, request.POST, instance=dept_obj)
    if form.is_valid():
        form.save()
        return redirect("departments")
    else:
        return departments_state_get(request, d, dept_obj, form=form)


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

    d = init_render_dict(request)
    d["confirm_form"] = {
        "title": f"Delete {dept_obj.name}",
        "text": ("Are you sure that you want to delete the"
                 f" department {dept_obj.name}?"),
        "return_url": "/departments"
    }
    return render(request, "confirm_form.html", d)
