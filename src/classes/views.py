from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.http import Http404

from mainpage.views import init_render_dict
from mainpage.models import Department

from users.models import Deptadmin, Teacher

from .models import Classes, PrerequisiteClasses, Teaching, ClassSignup
from .forms import ClassInsertForm, TeachingInsertForm


# ====================================================================
# Helpers
# ====================================================================

def render_dict_add_dept(t_dict, dept_id):
    obj = Department.objects.get(id=dept_id)
    t_dict.update({
        "dept": {
            "object": obj,
            "name": obj.name,
            "id": dept_id
        }
    })

    return t_dict


def render_dict_add_perm(t_dict, request, dept_id, class_id=False):
    user = request.user

    is_admin = False
    is_teacher = False

    if user.is_authenticated:
        if user.is_superuser:
            is_admin = True
        elif user.is_deptadmin:
            if Deptadmin.objects.get(user=user).department.id == dept_id:
                is_admin = True

    t_dict.update({
        "perm": {
            "is_admin": is_admin,
            "is_teacher": is_teacher
        }
    })

    return t_dict


def render_dict_add_class(t_dict, class_public_id):
    class_obj = Classes.objects.get(public_id=class_public_id)
    req_classes = PrerequisiteClasses.objects.filter(class_id=class_obj.id)
    teachings = Teaching.objects.filter(class_id=class_obj.id)
    class_signups = []
    for i in teachings:
        try:
            class_signups.append(ClassSignup.objects.get(teaching=i))
        except ClassSignup.DoesNotExist:
            pass

    t_dict.update({
        "class": {
            "object": class_obj,
            "id": class_obj.id,
            "name": class_obj.name,
            "description": class_obj.description,
            "public_id": class_public_id,
            "req_classes": req_classes,
            "teachings": teachings,
            "signups": class_signups
        }
    })

    return t_dict


# Form rendering =====================================================

def render_base_form(request, t_dict, form, title="Insert", submit_val="Save"):
    t_dict.update({
        "form": form,
        "t": {
            "title": title,
            "sumbit_value": submit_val
        }
    })
    return render(request, "base_form.html", t_dict)


# ====================================================================
# /departments/<int:dept_id>/classes
# ====================================================================

def classes(request, dept_id):
    d = init_render_dict(request)

    try:
        render_dict_add_dept(d, dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    render_dict_add_perm(d, request, dept_id)

    d["classes"] = Classes.objects.filter(department=dept_id)
    return render(request, "classes.html", d)


# ====================================================================
# /departments/<int:dept_id>/classes/insert
# ====================================================================

def insert(request, dept_id):
    try:
        d = render_dict_add_dept({}, dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    d = render_dict_add_perm(d, request, dept_id)

    if not d["perm"]["is_admin"]:
        raise PermissionDenied

    if request.method == "POST":
        return insert_post(request, d)

    return insert_get(request, d)


def insert_get(request, t_dict, form=False):
    dept_obj = t_dict["dept"]["object"]
    form = form if form else ClassInsertForm(
        dept_obj,
        instance=Classes(department=dept_obj)
    )
    t_dict.update({
        "form": form,
        "t": {
            "title": "Insert class",
            "sumbit_value": "Insert"
        }
    })

    return render(request, "base_form.html", t_dict)


def insert_post(request, t_dict):
    dept_obj = t_dict["dept"]["object"]
    dept_id = t_dict["dept"]["id"]

    form = ClassInsertForm(
        dept_obj,
        request.POST,
        instance=Classes(department=dept_obj)
    )
    if form.is_valid():
        form.save()
        return redirect("classes", dept_id=dept_id)
    else:
        return insert_get(request, t_dict, form)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# ====================================================================

def details(request, dept_id, class_public_id):
    d = init_render_dict(request)

    try:
        render_dict_add_dept(d, dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    render_dict_add_perm(d, request, dept_id)
    render_dict_add_class(d, class_public_id)

    return render(request, "classes_details.html", d)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>/delete
# ====================================================================

def delete(request, dept_id, class_public_id):
    try:
        d = render_dict_add_dept({}, dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    d = render_dict_add_perm(d, request, dept_id)
    d = render_dict_add_class(d, class_public_id)

    if not d["perm"]["is_admin"]:
        raise PermissionDenied

    if request.method == "POST":
        d["class"]["object"].delete()
        return redirect("classes", dept_id)

    return delete_get(request, d)


def delete_get(request, t_dict):
    dept_id = t_dict["dept"]["id"]
    class_name = t_dict["class"]["name"]

    t_dict["t"] = {
        "title": f"Delete {class_name}?",
        "confirm_text": ("Are you sure that you want to delete the class"
                         f" {class_name}?"),
        "return_url": f"/departments/{dept_id}/classes"
    }
    return render(request, "confirm_form.html", t_dict)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>/info/update
# ====================================================================

def info_update(request, dept_id, class_public_id):
    if request.method == "POST":
        return info_update_post(request, dept_id, class_public_id)

    return info_update_get(request, dept_id, class_public_id)


def info_update_get(request, dept_id, class_public_id):
    try:
        d = render_dict_add_dept({}, dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    d = render_dict_add_perm(d, request, dept_id)
    d = render_dict_add_class(d, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    dept_obj = d["dept"]["object"]
    class_obj = d["class"]["object"]
    form = ClassInsertForm(dept_obj, instance=class_obj)
    d.update({
        "form": form,
        "t": {
            "title": "Update class info",
            "sumbit_value": "Update"
        }
    })
    return render(request, "base_form.html", d)


def info_update_post(request, dept_id, class_public_id):
    try:
        d = render_dict_add_dept({}, dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    d = render_dict_add_perm(d, request, dept_id)
    d = render_dict_add_class(d, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    dept_obj = d["dept"]["object"]
    class_obj = d["class"]["object"]
    form = ClassInsertForm(dept_obj, request.POST, instance=class_obj)
    if form.is_valid():
        form.save()
        return redirect(
            "class",
            dept_id=dept_id,
            class_public_id=form.cleaned_data["public_id"]  # Use the new id.
        )
    else:
        d.update({
            "form": form,
            "t": {
                "title": "Update class info",
                "sumbit_value": "Update"
            }
        })
        return render(request, "base_form.html", d)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>/teaching/insert
# ====================================================================

def teaching_insert(request, dept_id, class_public_id):
    if request.method == "POST":
        return teaching_insert_post(request, dept_id, class_public_id)

    return teaching_insert_get(request, dept_id, class_public_id)


def teaching_insert_get(request, dept_id, class_public_id):
    d = render_dict_add_perm({}, request, dept_id)

    if not d["perm"]["is_admin"]:
        raise PermissionDenied

    form = TeachingInsertForm(dept_id, "admin_insert")
    return render_base_form(
        request, d, form, title="Insert class", submit_val="Insert")


def teaching_insert_post(request, dept_id, class_public_id):
    d = render_dict_add_perm({}, request, dept_id)

    if not d["perm"]["is_admin"]:
        raise PermissionDenied

    class_obj = Classes.objects.get(public_id=class_public_id)
    teaching = Teaching(class_id=class_obj)

    form = TeachingInsertForm(
        dept_id, "admin_insert", request.POST, instance=teaching)

    if form.is_valid():
        form.save()
        return redirect(
            "class", dept_id=dept_id, class_public_id=class_public_id
        )
    else:
        return render_base_form(
            request, d, form, title="Insert class", submit_val="Insert")


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/update
# ====================================================================

def teaching_update(request, dept_id, class_public_id, teaching_id):
    if request.method == "POST":
        return teaching_update_post(
            request, dept_id, class_public_id, teaching_id
        )

    return teaching_update_get(request, dept_id, class_public_id, teaching_id)


def teaching_update_get(request, dept_id, class_public_id, teaching_id):
    d = render_dict_add_perm({}, request, dept_id)

    if d["perm"]["is_admin"]:
        form_mode = "admin_update"
    elif d["perm"]["is_teacher"]:
        form_mode = "teacher_update"
    else:
        raise PermissionDenied

    teaching_obj = Teaching.objects.get(id=teaching_id)

    form = TeachingInsertForm(dept_id, form_mode, instance=teaching_obj)
    return render_base_form(request, d, form, title="Update teaching")


def teaching_update_post(request, dept_id, class_public_id, teaching_id):
    d = render_dict_add_perm({}, request, dept_id)

    if d["perm"]["is_admin"]:
        form_mode = "admin_update"
    elif d["perm"]["is_teacher"]:
        form_mode = "teacher_update"
    else:
        raise PermissionDenied

    teaching_obj = Teaching.objects.get(id=teaching_id)

    form = TeachingInsertForm(
        dept_id, form_mode, request.POST, instance=teaching_obj)

    if form.is_valid():
        form.save()
        return redirect(
            "class",
            dept_id=dept_id,
            class_public_id=class_public_id
        )
    else:
        return render_base_form(request, d, form, title="Update teaching")


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/delete
# ====================================================================

def teaching_delete(request, dept_id, class_public_id, teaching_id):
    if request.method == "POST":
        return teaching_delete_post(
            request, dept_id, class_public_id, teaching_id
        )

    return teaching_delete_get(request, dept_id, class_public_id, teaching_id)


def teaching_delete_get(request, dept_id, class_public_id, teaching_id):
    d = render_dict_add_perm({}, request, dept_id)

    if not d["perm"]["is_admin"]:
        raise PermissionDenied

    teaching_obj = Teaching.objects.get(id=teaching_id)

    d["t"] = {
        "title": "Delete teaching?",
        "confirm_text": ("Are you sure that you want to delete the"
                         f" {teaching_obj.year} teaching?"),
        "return_url": f"/departments/{dept_id}/classes/{class_public_id}"
    }
    return render(request, "confirm_form.html", d)


def teaching_delete_post(request, dept_id, class_public_id, teaching_id):
    d = render_dict_add_perm({}, request, dept_id)

    if not d["perm"]["is_admin"]:
        raise PermissionDenied

    Teaching.objects.filter(id=teaching_id).delete()
    return redirect("class", dept_id, class_public_id)
