from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied

from mainpage.models import Department

from users.models import Deptadmin, Teacher

from .models import Classes, PrerequisiteClasses, Teaching, ClassSignup
from .forms import ClassInsertForm, TeachingInsertForm


# ====================================================================
# Helpers
# ====================================================================

def init_render_dict(request, dept_id, class_id=False):
    user = request.user

    is_admin = False
    if user.is_superuser:
        is_admin = True
    elif user.is_deptadmin:
        if Deptadmin.objects.get(user=user).department.id == dept_id:
            is_admin = True

    t_dict = {
        "is_admin": is_admin,
        "dept_name": Department.objects.get(id=dept_id).name,
        "dept_id": dept_id
    }

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


# ====================================================================
# /departments/<int:dept_id>/classes
# ====================================================================

def classes(request, dept_id=None):
    if request.method == "POST":
        return classes_post(request, dept_id)

    if request.user.is_superuser:
        t_dict = init_render_dict(request, dept_id)
        t_dict["classes"] = Classes.objects.filter(department=dept_id)
        return render(request, "classes.html", t_dict)


def classes_post(request, dept_id):
    if request.POST.get("action") == "insert":

        if request.user.is_superuser:
            t_dict = init_render_dict(request, dept_id)
            form = ClassInsertForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect(f"/departments/{dept_id}/classes")
            else:
                t_dict["form"] = form
                return render(request, "classes_insert.html", t_dict)


# ====================================================================
# /departments/<int:dept_id>/classes/insert
# ====================================================================

def insert(request, dept_id=None):
    if request.user.is_superuser:
        t_dict = init_render_dict(request, dept_id)
        t_dict["form"] = ClassInsertForm(
            initial={"department": t_dict["dept_id"]}
        )
        return render(request, "classes_insert.html", t_dict)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# ====================================================================

def details(request, dept_id, class_public_id):
    t_dict = init_render_dict(request, dept_id)
    render_dict_add_class(t_dict, class_public_id)
    return render(request, "classes_details.html", t_dict)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>/delete
# ====================================================================

def delete(request, dept_id, class_public_id):
    if request.method == "GET":
        return delete_get(request, dept_id, class_public_id)

    if request.method == "POST":
        return delete_post(request, dept_id, class_public_id)


def delete_get(request, dept_id, class_public_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)

    if t_dict.get("is_admin"):
        class_obj = Classes.objects.get(public_id=class_public_id)
        t_dict["t"] = {
            "title": f"Delete {class_obj.name}?",
            "confirm_text": ("Are you sure that you want to delete the class"
                             f" {class_obj.name}?"),
            "return_url": f"/departments/{dept_id}/classes"
        }
        return render(request, "classes_confirm_form.html", t_dict)

    raise PermissionDenied


def delete_post(request, dept_id, class_public_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)

    if t_dict.get("is_admin"):
        Classes.objects.filter(public_id=class_public_id).delete()
        return redirect("classes", dept_id)

    raise PermissionDenied


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>/info/update
# ====================================================================

def info_update(request, dept_id, class_public_id):
    if request.method == "GET":
        return info_update_get(request, dept_id, class_public_id)

    if request.method == "POST":
        return info_update_post(request, dept_id, class_public_id)


def info_update_get(request, dept_id, class_public_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)
    render_dict_add_class(t_dict, class_public_id)

    if t_dict.get("is_admin") or t_dict.get("is_teacher"):
        class_obj = t_dict["class"]["object"]
        form = ClassInsertForm(instance=class_obj)
        t_dict["form"] = form
        return render(request, "classes_info_update.html", t_dict)


def info_update_post(request, dept_id, class_public_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)
    render_dict_add_class(t_dict, class_public_id)

    if t_dict.get("is_admin") or t_dict.get("is_teacher"):
        class_obj = t_dict["class"]["object"]
        form = ClassInsertForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            return redirect(
                "class",
                dept_id=form.cleaned_data["department"].id,
                class_public_id=form.cleaned_data["public_id"]
            )
        else:
            t_dict["form"] = form
            return render(request, "classes_info_update.html", t_dict)

    raise PermissionDenied


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>/teaching/insert
# ====================================================================

def teaching_insert(request, dept_id, class_public_id):
    if request.method == "GET":
        return teaching_insert_get(request, dept_id, class_public_id)

    if request.method == "POST":
        return teaching_insert_post(request, dept_id, class_public_id)


def teaching_insert_get(request, dept_id, class_public_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)
    render_dict_add_class(t_dict, class_public_id)

    if t_dict.get("is_admin"):
        form = TeachingInsertForm(dept_id, "admin_insert")
        t_dict["form"] = form
        t_dict["t"] = {"title": "Insert teaching"}
        return render(request, "classes_base_form.html", t_dict)

    raise PermissionDenied


def teaching_insert_post(request, dept_id, class_public_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)
    render_dict_add_class(t_dict, class_public_id)

    if t_dict.get("is_admin"):
        class_obj = t_dict["class"]["object"]
        teaching = Teaching(class_id=class_obj)

        form = TeachingInsertForm(
            dept_id, "admin_insert", request.POST, instance=teaching)

        if form.is_valid():
            form.save()
            return redirect(
                "class", dept_id=dept_id, class_public_id=class_public_id
            )
        else:
            t_dict["form"] = form
            t_dict["t"] = {"title": "Insert teaching"}
            return render(request, "classes_base_form.html", t_dict)

    raise PermissionDenied


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/update
# ====================================================================

def teaching_update(request, dept_id, class_public_id, teaching_id):
    if request.method == "GET":
        return teaching_update_get(
            request, dept_id, class_public_id, teaching_id
        )

    if request.method == "POST":
        return teaching_update_post(
            request, dept_id, class_public_id, teaching_id
        )


def teaching_update_get(request, dept_id, class_public_id, teaching_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)
    render_dict_add_class(t_dict, class_public_id)

    if t_dict.get("is_admin") or t_dict.get("is_teacher"):
        teaching_obj = Teaching.objects.get(id=teaching_id)

        if t_dict.get("is_admin"):
            form_mode = "admin_update"
        elif t_dict.get("is_teacher"):
            form_mode = "teacher_update"

        form = TeachingInsertForm(dept_id, form_mode, instance=teaching_obj)
        t_dict["form"] = form
        t_dict["t"] = {"title": "Update teaching"}
        return render(request, "classes_base_form.html", t_dict)

    raise PermissionDenied


def teaching_update_post(request, dept_id, class_public_id, teaching_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)
    render_dict_add_class(t_dict, class_public_id)

    if t_dict.get("is_admin") or t_dict.get("is_teacher"):
        teaching_obj = Teaching.objects.get(id=teaching_id)

        if t_dict.get("is_admin"):
            form_mode = "admin_update"
        elif t_dict.get("is_teacher"):
            form_mode = "teacher_update"

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
            t_dict["form"] = form
            t_dict["t"] = {"title": "Update teaching"}
            return render(request, "classes_info_update.html", t_dict)

    raise PermissionDenied


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/delete
# ====================================================================

def teaching_delete(request, dept_id, class_public_id, teaching_id):
    if request.method == "GET":
        return teaching_delete_get(
            request, dept_id, class_public_id, teaching_id
        )

    if request.method == "POST":
        return teaching_delete_post(
            request, dept_id, class_public_id, teaching_id
        )


def teaching_delete_get(request, dept_id, class_public_id, teaching_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)

    if t_dict.get("is_admin"):
        teaching_obj = Teaching.objects.get(id=teaching_id)
        t_dict["t"] = {
            "title": "Delete teaching?",
            "confirm_text": ("Are you sure that you want to delete the"
                             f" {teaching_obj.year} teaching?"),
            "return_url": f"/departments/{dept_id}/classes/{class_public_id}"
        }
        return render(request, "classes_confirm_form.html", t_dict)

    raise PermissionDenied


def teaching_delete_post(request, dept_id, class_public_id, teaching_id):
    t_dict = init_render_dict(request, dept_id, class_id=class_public_id)

    if t_dict.get("is_admin"):
        Teaching.objects.filter(id=teaching_id).delete()
        return redirect("class", dept_id, class_public_id)

    raise PermissionDenied
