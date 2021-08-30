import csv

from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.db.models import Max

from mainpage.views import init_render_dict, render_dict_add_perm
from mainpage.models import Department

from users.models import Teacher

from .models import Classes, PrerequisiteClasses, Teaching, ClassSignup
from .forms import (
    ClassInsertForm, ClassDescriptionForm, PrerequisiteClassForm,
    TeachingInsertForm, GradeUpdateForm, GradeUnlockForm, GradesCSVFileForm
)


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

def render_base_form(request, d, form, title="Insert", submit_val="Save"):
    d["base_form"] = {
        "form": form,
        "title": title,
        "submit_value": submit_val
    }
    return render(request, "base_form.html", d)


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


def insert_get(request, d, form=False):
    d.update(init_render_dict(request))
    dept_obj = d["dept"]["object"]
    form = form if form else ClassInsertForm(
        dept_obj,
        instance=Classes(department=dept_obj)
    )
    return render_base_form(
        request, d, form, title="Insert class", submit_val="Insert")


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

    render_dict_add_perm(d, request, dept_id, class_public_id)
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

    t_dict["confirm_form"] = {
        "title": f"Delete {class_name}?",
        "text": f"Delete the class {class_name}?",
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

    d.update(init_render_dict(request))
    d = render_dict_add_perm(d, request, dept_id, class_public_id)
    d = render_dict_add_class(d, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    dept_obj = d["dept"]["object"]
    class_obj = d["class"]["object"]
    if d["perm"]["is_admin"]:
        form = ClassInsertForm(dept_obj, instance=class_obj)
    elif d["perm"]["is_teacher"]:
        form = ClassDescriptionForm(instance=class_obj)

    return render_base_form(
        request, d, form, title="Update class info", submit_val="Update")


def info_update_post(request, dept_id, class_public_id):
    try:
        d = render_dict_add_dept({}, dept_id)
    except Department.DoesNotExist:
        raise Http404(f"No department with id {dept_id}")

    d = render_dict_add_perm(d, request, dept_id, class_public_id)
    d = render_dict_add_class(d, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    dept_obj = d["dept"]["object"]
    class_obj = d["class"]["object"]
    if d["perm"]["is_admin"]:
        form = ClassInsertForm(dept_obj, request.POST, instance=class_obj)
        new_public_id = form.cleaned_data["public_id"]  # Use the new id.
    elif d["perm"]["is_teacher"]:
        form = ClassDescriptionForm(request.POST, instance=class_obj)
        new_public_id = class_public_id

    if form.is_valid():
        form.save()
        return redirect(
            "class",
            dept_id=dept_id,
            class_public_id=new_public_id
        )
    else:
        d.update(init_render_dict(request))
        return render_base_form(
            request, d, form, title="Update class info", submit_val="Update")


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>/prerequisites/insert
# ====================================================================

def prerequisites_insert(request, dept_id, class_public_id):
    if request.method == "POST":
        return prerequisites_insert_post(request, dept_id, class_public_id)

    return prerequisites_insert_get(request, dept_id, class_public_id)


def prerequisites_insert_get(request, dept_id, class_public_id):
    d = init_render_dict(request)
    d = render_dict_add_dept(d, dept_id)
    d = render_dict_add_perm(d, request, dept_id, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    class_obj = Classes.objects.get(public_id=class_public_id)
    form = PrerequisiteClassForm(
        class_obj,
        instance=PrerequisiteClasses(class_id=class_obj))
    return render_base_form(
        request, d, form, title="Add prerequisite class", submit_val="Add")


def prerequisites_insert_post(request, dept_id, class_public_id):
    d = render_dict_add_perm({}, request, dept_id, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    class_obj = Classes.objects.get(public_id=class_public_id)
    form = PrerequisiteClassForm(
        class_obj,
        request.POST,
        instance=PrerequisiteClasses(class_id=class_obj))
    if form.is_valid():
        form.save()
        return redirect(
            "class", dept_id=dept_id, class_public_id=class_public_id
        )
    else:
        return render_base_form(
            request, d, form, title="Add prerequisite class", submit_val="Add")


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /prerequisites/<int:req_id>/delete
# ====================================================================

def prerequisites_delete(request, dept_id, class_public_id, req_id):
    if request.method == "POST":
        return prerequisites_delete_post(
            request, dept_id, class_public_id, req_id
        )

    return prerequisites_delete_get(request, dept_id, class_public_id, req_id)


def prerequisites_delete_get(request, dept_id, class_public_id, req_id):
    d = init_render_dict(request)
    d = render_dict_add_dept(d, dept_id)
    d = render_dict_add_perm(d, request, dept_id, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    d["confirm_form"] = {
        "title": "Delete teaching?",
        "text": ("Are you sure that you want to delete this"
                 " prerequisite class?"),
        "return_url": f"/departments/{dept_id}/classes/{class_public_id}"
    }
    return render(request, "confirm_form.html", d)


def prerequisites_delete_post(request, dept_id, class_public_id, req_id):
    d = render_dict_add_perm({}, request, dept_id, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    PrerequisiteClasses.objects.filter(id=req_id).delete()
    return redirect("class", dept_id, class_public_id)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>/teaching/insert
# ====================================================================

def teaching_insert(request, dept_id, class_public_id):
    if request.method == "POST":
        return teaching_insert_post(request, dept_id, class_public_id)

    return teaching_insert_get(request, dept_id, class_public_id)


def teaching_insert_get(request, dept_id, class_public_id):
    d = init_render_dict(request)
    d = render_dict_add_dept(d, dept_id)
    d = render_dict_add_perm(d, request, dept_id)

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
    d = init_render_dict(request)
    d = render_dict_add_dept(d, dept_id)
    d = render_dict_add_perm(d, request, dept_id, class_public_id)

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
    d = render_dict_add_perm({}, request, dept_id, class_public_id)

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
    d = init_render_dict(request)
    d = render_dict_add_dept(d, dept_id)
    d = render_dict_add_perm(d, request, dept_id)

    if not d["perm"]["is_admin"]:
        raise PermissionDenied

    teaching_obj = Teaching.objects.get(id=teaching_id)

    d["confirm_form"] = {
        "title": "Delete teaching?",
        "text": ("Are you sure that you want to delete the"
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


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/grades
# ====================================================================

def grades(request, dept_id, class_public_id, teaching_id):
    d = init_render_dict(request)
    d = render_dict_add_dept(d, dept_id)
    d = render_dict_add_perm(d, request, dept_id, class_public_id)
    d = render_dict_add_class(d, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    teaching = Teaching.objects.get(id=teaching_id)
    signups = ClassSignup.objects.filter(teaching=teaching)
    d.update({
        "teaching": {"id": teaching_id},
        "signups": []
    })
    for signup in signups:
        t_pr_year, t_pr_grade = ClassSignup.get_previous_theory_grade(signup)
        l_pr_year, l_pr_grade = ClassSignup.get_previous_lab_grade(signup)
        d["signups"].append({
            "id": signup.id,
            "registry_id": signup.student.registry_id,
            "first_name": signup.student.first_name,
            "last_name": signup.student.last_name,
            "theory_grade": signup.theory_mark,
            "lab_grade": signup.lab_mark,
            "final_mark": signup.final_mark,
            "locked": signup.locked,
            "theory_prev_grade": t_pr_grade,
            "theory_prev_year": t_pr_year,
            "lab_prev_grade": l_pr_grade,
            "lab_prev_year": l_pr_year
        })
    return render(request, "classes_grades.html", d)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/grades/upload
# ====================================================================

def grades_upload(request, dept_id, class_public_id, teaching_id):
    d = init_render_dict(request)
    d = render_dict_add_dept(d, dept_id)
    d = render_dict_add_perm(d, request, dept_id, class_public_id)

    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    teaching = Teaching.objects.get(id=teaching_id)
    if request.method == "POST":
        form = GradesCSVFileForm(teaching, request.POST, request.FILES)
        if form.is_valid():
            form.handle(request.FILES["file"])
            return redirect("grades", dept_id, class_public_id, teaching_id)
    else:
        form = GradesCSVFileForm(teaching)

    d.update({"form": form})
    return render(request, "classes_csv_upload.html", d)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/grades/apply_previous
# ====================================================================

def grades_apply_previous(request, dept_id, class_public_id, teaching_id):
    d = render_dict_add_perm({}, request, dept_id, class_public_id)
    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    signups = ClassSignup.objects.filter(teaching__id=teaching_id)
    for signup in signups:
        if signup.locked:
            continue
        t_pr_year, t_pr_grade = ClassSignup.get_previous_theory_grade(signup)
        l_pr_year, l_pr_grade = ClassSignup.get_previous_lab_grade(signup)
        if t_pr_grade and l_pr_grade:
            classes.forms.apply_grade(signup, t_pr_grade, l_pr_grade)
    return redirect("grades", dept_id, class_public_id, teaching_id)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/grades/finalize
# ====================================================================

def grades_finalize(request, dept_id, class_public_id, teaching_id):
    d = init_render_dict(request)
    d = render_dict_add_perm(d, request, dept_id, class_public_id)
    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    signups = ClassSignup.objects.filter(
        teaching__id=teaching_id, locked=False
    )
    errors = []
    for signup in signups:
        if not signup.theory_mark or not signup.lab_mark \
           or not signup.final_mark:
            errors.append(signup.student.registry_id)
        else:
            signup.locked = True
            signup.save()

    if errors:
        d.update({
            "title": "Finalization errors",
            "message": ("The grades for the following users could not be"
                        " finalized. Please review them and retry."
                        f' {", ".join(errors)}'),
            "url": (f"/departments/{dept_id}"
                    f"/classes/{class_public_id}"
                    f"/teaching/{teaching_id}"
                    "/grades")
        })
        return render(request, "info_dialog.html", d)

    return redirect("grades", dept_id, class_public_id, teaching_id)


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/export/grades
# ====================================================================

def export_grades(request, dept_id, class_public_id, teaching_id):
    d = render_dict_add_perm({}, request, dept_id, class_public_id)
    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="grades.csv"'}
    )
    writer = csv.writer(response)

    signups = ClassSignup.objects.filter(teaching__id=teaching_id)
    for i in signups:
        writer.writerow([
            i.student.registry_id, i.student.first_name, i.student.last_name,
            i.theory_mark, i.lab_mark, i.final_mark
        ])

    return response


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/export/signups
# ====================================================================

def export_signups(request, dept_id, class_public_id, teaching_id):
    d = render_dict_add_perm({}, request, dept_id, class_public_id)
    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="signups.csv"'}
    )
    writer = csv.writer(response)

    signups = ClassSignup.objects.filter(teaching__id=teaching_id)
    for i in signups:
        writer.writerow([
            i.student.registry_id, i.student.first_name, i.student.last_name,
            i.student.user.email
        ])

    return response


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/grades/<int:grade_id>/update
# ====================================================================

def grade_update(request, dept_id, class_public_id, teaching_id, grade_id):
    d = render_dict_add_perm({}, request, dept_id, class_public_id)
    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    if request.method == "POST":
        return grade_update_post(
            request, dept_id, class_public_id, teaching_id, grade_id
        )

    return grade_update_get(
        request, dept_id, class_public_id, teaching_id, grade_id)


def grade_update_get(request, dept_id, class_public_id, teaching_id, grade_id):
    d = init_render_dict(request)
    d = render_dict_add_dept(d, dept_id)
    d = render_dict_add_perm(d, request, dept_id, class_public_id)

    signup = ClassSignup.objects.get(id=grade_id)
    if signup.locked:
        d.update({
            "title": "Finalization errors",
            "message": ("The grades for this signup are locked."
                        f' (student: {signup.student.registry_id})'),
            "url": (f"/departments/{dept_id}/classes/{class_public_id}"
                    f"/teaching/{teaching_id}/grades")
        })
        return render(request, "info_dialog.html", d)

    form = GradeUpdateForm(instance=signup)
    return render_base_form(
        request, d, form, title="Update grade", submit_val="Save")


def grade_update_post(request, dept_id, class_public_id, teaching_id,
                      grade_id):
    signup = ClassSignup.objects.get(id=grade_id)
    if signup.locked:
        d = init_render_dict(request)
        d.update({
            "title": "Finalization errors",
            "message": ("The grades for this signup are locked."
                        f' (student: {signup.student.registry_id})'),
            "url": (f"/departments/{dept_id}/classes/{class_public_id}"
                    f"/teaching/{teaching_id}/grades")
        })
        return render(request, "info_dialog.html", d)

    form = GradeUpdateForm(request.POST,
                           instance=signup)
    if form.is_valid():
        form.save()
        return redirect("grades", dept_id, class_public_id, teaching_id)
    else:
        d = init_render_dict(request)
        d = render_dict_add_dept(d, dept_id)
        d = render_dict_add_perm(d, request, dept_id, class_public_id)
        return render_base_form(
            request, d, form, title="Update mark", submit_val="Save")


# ====================================================================
# /departments/<int:dept_id>/classes/<int:class_public_id>
# /teaching/<int:teaching_id>/grades/<int:grade_id>/unlock
# ====================================================================

def grade_unlock(request, dept_id, class_public_id, teaching_id, grade_id):
    d = render_dict_add_perm({}, request, dept_id, class_public_id)
    if not (d["perm"]["is_admin"] or d["perm"]["is_teacher"]):
        raise PermissionDenied

    signup = ClassSignup.objects.get(id=grade_id)
    form = GradeUnlockForm(request.POST, instance=signup)
    if form.is_valid():
        form.save()
        return redirect("grades", dept_id, class_public_id, teaching_id)
    else:
        # The following should never be shown. If it is there is an error
        # with the way the form is rendered or validated.
        return render_base_form(
            request, d, form, title="Unlock grade", submit_val="Save")


# ====================================================================
# /users/<int:user_id>/teachings
# ====================================================================

def my_teachings(request, user_id):
    d = init_render_dict(request)

    if not d["user"].get("is_teacher"):
        return Http404()

    dept_id = d["user"]["teacher"]["departments"][0].dept_id.id
    d = render_dict_add_dept(d, dept_id)

    teacher = Teacher.objects.get(user=d["user"]["object"])
    year = Teaching.objects.aggregate(Max("year"))["year__max"]
    teachings = Teaching.objects.filter(
        teacher=teacher, year=year).select_related("class_id")
    d["teachings"] = teachings
    return render(request, "classes_my_teachings.html", d)
