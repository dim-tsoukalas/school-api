from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm

from mainpage.views import init_render_dict
from mainpage.models import States, DepartmentStudents, DepartmentTeachers

from classes.models import ClassSignup

from .models import User, Teacher, Student, Deptadmin
from .forms import (
    UserActionForm, UserEmailForm,
    StudentSignupForm, StudentUpdateForm, StudentClassSignupForm,
    TeacherSignupForm, TeacherUpdateForm,
    DeptadminSignupForm, DeptadminUpdateForm,
    SigninForm
)


# ====================================================================
# Helpers
# ====================================================================

def has_perm_deptadmin(request, uid):
    dept = Deptadmin.objects.get(user=request.user).department
    is_student_in_dept = DepartmentStudents.objects.filter(
        dept_id=dept, user_id__id=uid).exists()
    is_teacher_in_dept = DepartmentTeachers.objects.filter(
        dept_id=dept, user_id__id=uid).exists()
    return is_student_in_dept or is_teacher_in_dept


def get_user_type(uid):
    if Student.objects.filter(user__id=uid).exists():
        return "student"
    elif Teacher.objects.filter(user__id=uid).exists():
        return "teacher"
    elif Deptadmin.objects.filter(user__id=uid).exists():
        return "deptadmin"


def get_department(uid, user_type):
    if user_type == "student":
        return DepartmentStudents.objects.get(user_id__id=uid).dept_id

    if user_type == "teacher":
        return DepartmentTeachers.objects.get(user_id__id=uid).dept_id

    if user_type == "deptadmin":
        return Deptadmin.objects.get(user_id__id=uid).department_id


# User update form ===================================================

def get_user_update_form(uid, method_data=None):
    user_type = get_user_type(uid)

    if user_type == "student":
        class_ref = StudentUpdateForm
    elif user_type == "teacher":
        class_ref = TeacherUpdateForm
    elif user_type == "deptadmin":
        class_ref = DeptadminUpdateForm

    user = User.objects.get(id=uid)

    if method_data:
        return class_ref(method_data, instance=user)
    else:
        initial = get_user_update_form_initial(uid, user_type)
        return class_ref(initial=initial, instance=user)


def get_user_update_form_initial(uid, user_type):
    if user_type == "student":
        return get_user_update_form_initial_student(uid)
    elif user_type == "teacher":
        return get_user_update_form_initial_teacher(uid)
    elif user_type == "deptadmin":
        return get_user_update_form_initial_deptadmin(uid)


def get_user_update_form_initial_student(uid):
    student = Student.objects.get(user__id=uid)
    department = DepartmentStudents.objects.get(user_id__id=uid).dept_id

    return {
        "department": department,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "registry_id": student.registry_id,
        "admission_year": student.admission_year,
    }


def get_user_update_form_initial_teacher(uid):
    teacher = Teacher.objects.get(user__id=uid)
    department = DepartmentTeachers.objects.get(user_id__id=uid).dept_id

    return {
        "department": department,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "rank": teacher.rank,
    }


def get_user_update_form_initial_deptadmin(uid):
    deptadmin = Deptadmin.objects.get(user__id=uid)

    return {
        "department": deptadmin.department,
    }


# ====================================================================

def make_user_data_student(user, student):
    departments = DepartmentStudents.objects.filter(user_id=user.id)
    departments = ", ".join([x.dept_id.name for x in departments])

    return {
        "type": "student",
        "user_id": user.id,
        "is_accepted": user.is_accepted,
        "is_active": user.is_active,
        "registry_id": student.registry_id,
        "email": user.email,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "admission_year": student.admission_year,
        "departments": departments
    }


def make_user_data_teacher(user, teacher):
    departments = DepartmentTeachers.objects.filter(user_id=user.id)
    departments = ", ".join([x.dept_id.name for x in departments])

    return {
        "type": "teacher",
        "user_id": user.id,
        "is_accepted": user.is_accepted,
        "is_active": user.is_active,
        "email": user.email,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "rank": teacher.rank,
        "departments": departments
    }


def make_user_data_deptadmin(user, deptadmin):
    return {
        "type": "deptadmin",
        "user_id": user.id,
        "is_accepted": user.is_accepted,
        "is_active": user.is_active,
        "email": user.email,
        "departments": deptadmin.department.name
    }


def make_table_students(students):
    rows = []
    for student in students:
        rows.append(make_user_data_student(student.user, student))
    return rows


def make_table_students_dept(department):
    query = DepartmentStudents.objects.filter(
        dept_id=department).select_related("user_id")
    rows = []
    for i in query:
        student = Student.objects.get(user=i.user_id)
        rows.append(make_user_data_student(student.user, student))
    return rows


def make_table_teachers(teachers):
    rows = []
    for teacher in teachers:
        rows.append(make_user_data_teacher(teacher.user, teacher))
    return rows


def make_table_teachers_dept(department):
    query = DepartmentTeachers.objects.filter(
        dept_id=department).select_related("user_id")
    rows = []
    for i in query:
        teacher = Teacher.objects.get(user=i.user_id)
        rows.append(make_user_data_student(teacher.user, teacher))
    return rows


def make_table_deptadmins(deptadmins):
    rows = []
    for admin in deptadmins:
        rows.append(make_user_data_deptadmin(admin.user, admin))
    return rows


# ====================================================================
# /users
# ====================================================================

def users(request):
    d = init_render_dict(request)

    if not d["user"]["is_superuser"] and not d["user"].get("is_deptadmin"):
        raise PermissionDenied

    if request.user.is_superuser:
        d.update({
            "students": make_table_students(Student.objects.all()),
            "teachers": make_table_teachers(Teacher.objects.all()),
            "deptadmins": make_table_deptadmins(Deptadmin.objects.all())
        })
        return render(request, "users.html", d)
    elif request.user.is_deptadmin:
        dept = d["user"]["deptadmin"]["department"]
        d.update({
            "students": make_table_students_dept(dept),
            "teachers": make_table_teachers(Teacher.objects.all())
        })
        return render(request, "users.html", d)


# ====================================================================
# /users/insert/deptadmin
# ====================================================================

def insert_deptadmin(request):
    d = init_render_dict(request)

    if not d["user"]["is_superuser"]:
        raise PermissionDenied

    if request.method == "POST":
        return insert_deptadmin_post(request, d)

    return insert_deptadmin_get(request, d)


def insert_deptadmin_get(request, d, form=None):
    d["base_form"] = {
        "form": form if form else DeptadminSignupForm(),
        "title": "Insert department admin",
        "submit_value": "Insert"
    }
    return render(request, "base_form.html", d)


def insert_deptadmin_post(request, d):
    form = DeptadminSignupForm(request.POST)
    if form.is_valid():
        user = form.save()
        user.is_accepted = True
        user.save()
        return redirect("users")
    else:
        return insert_teacher_get(request, d, form=form)


# ====================================================================
# /users/insert/teacher
# ====================================================================

def insert_teacher(request):
    d = init_render_dict(request)

    if not d["user"]["is_superuser"] and not d["user"].get("is_deptadmin"):
        raise PermissionDenied

    if request.method == "POST":
        return insert_teacher_post(request, d)

    return insert_teacher_get(request, d)


def insert_teacher_get(request, d, form=None):
    d["base_form"] = {
        "title": "Insert teacher",
        "submit_value": "Insert"
    }
    if form:
        d["base_form"]["form"] = form
    elif request.user.is_superuser:
        d["base_form"]["form"] = TeacherSignupForm()
    elif d["user"].get("is_deptadmin"):
        f = TeacherSignupForm()
        del f.fields["department"]
        d["base_form"]["form"] = f

    return render(request, "base_form.html", d)


def insert_teacher_post(request, d):
    data = request.POST.copy()  # Get a mutable copy

    if d["user"].get("is_deptadmin"):
        dept_id = d["user"]["deptadmin"]["department"].id
        data["department"] = str(dept_id)

    form = TeacherSignupForm(data)
    if form.is_valid():
        user = form.save()
        user.is_accepted = True
        user.save()
        return redirect("users")
    else:
        if d["user"].get("is_deptadmin"):
            del form.fields["department"]

        return insert_teacher_get(request, d, form=form)


# ====================================================================
# /users/insert/student
# ====================================================================

def insert_student(request):
    d = init_render_dict(request)

    if not d["user"]["is_superuser"] and not d["user"].get("is_deptadmin"):
        raise PermissionDenied

    if request.method == "POST":
        return insert_student_post(request, d)

    return insert_student_get(request, d)


def insert_student_get(request, d, form=None):
    d["base_form"] = {
        "title": "Insert student",
        "submit_value": "Insert"
    }

    if form:
        d["base_form"]["form"] = form
    elif request.user.is_superuser:
        d["base_form"]["form"] = StudentSignupForm()
    elif d["user"].get("is_deptadmin"):
        f = StudentSignupForm()
        del f.fields["department"]
        d["base_form"]["form"] = f

    return render(request, "base_form.html", d)


def insert_student_post(request, d):
    data = request.POST.copy()  # Get a mutable copy

    if d["user"].get("is_deptadmin"):
        dept_id = d["user"]["deptadmin"]["department"].id
        data["department"] = str(dept_id)

    form = StudentSignupForm(data)
    if form.is_valid():
        user = form.save()
        user.is_accepted = True
        user.save()
        return redirect("users")
    else:
        if d["user"].get("is_deptadmin"):
            del form.fields["department"]

        return insert_student_get(request, d, form=form)


# ====================================================================
# /users/<int:id>/update
# ====================================================================

def update(request, uid):
    d = init_render_dict(request)

    if d["user"].get("id") == uid:
        return update_self(request, uid, d)
    elif request.user.is_superuser:
        return update_superuser(request, uid, d)
    elif d["user"].get("is_deptadmin"):
        # Ensure that the deptadmin is allowed to edit this user.
        if not has_perm_deptadmin(request, uid):
            raise PermissionDenied
        return update_deptadmin(request, uid, d)
    else:
        raise PermissionDenied


def update_self(request, uid, d):
    if request.method == "POST":
        return update_self_post(request, uid, d)

    return update_self_get(request, uid, d)


def update_self_get(request, uid, d, email_form=None, pass_form=None):
    email_form = email_form if email_form else UserEmailForm(
        instance=request.user)
    pass_form = pass_form if pass_form else PasswordChangeForm(request.user)

    d = init_render_dict(request)
    d.update({
        "settings_email": {
            "form": email_form
        },
        "settings_password": {
            "form": pass_form
        }
    })
    return render(request, "users_update_self.html", d)


def update_self_post(request, uid, d):
    if request.POST.get("mode") == "email":
        form = UserEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("users_update", uid)
        else:
            return update_self_get(request, uid, d, email_form=form)
    elif request.POST.get("mode") == "password":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect("home")
        else:
            return update_self_get(request, uid, d, pass_form=form)


def update_superuser(request, uid, d):
    if request.method == "POST":
        form = get_user_update_form(uid, method_data=request.POST)
        if form.is_valid():
            form.save()
            return redirect("users")
    else:
        form = get_user_update_form(uid)

    user_type = get_user_type(uid)
    return render_update_form(request, d, form, title=f"Update {user_type}")


def update_deptadmin(request, uid, d):
    if request.method == "POST":
        data = request.POST.copy()  # Get a mutable copy
        dept_id = d["user"]["deptadmin"]["department"].id
        data["department"] = str(dept_id)  # Sticky department
        form = get_user_update_form(uid, method_data=data)
        if form.is_valid():
            form.save()
            return redirect("users")
    else:
        form = get_user_update_form(uid)

    del form.fields["department"]  # Deptadmins cannot change the department
    user_type = get_user_type(uid)
    return render_update_form(request, d, form, title=f"Update {user_type}")


def render_update_form(request, d, form, title="Update user"):
    d["base_form"] = {
            "form": form,
            "title": title,
            "submit_value": "Save"
        }
    return render(request, "base_form.html", d)


# ====================================================================
# /users/<int:id>/accept
# ====================================================================

def accept(request, uid):
    if request.method != "POST":
        raise PermissionDenied

    d = init_render_dict(request)

    if not d["user"]["is_superuser"] and not d["user"].get("is_deptadmin"):
        raise PermissionDenied

    if d["user"].get("is_deptadmin") and not has_perm_deptadmin(request, uid):
        raise PermissionDenied

    form = UserActionForm({"user_id": uid})
    if form.is_valid():
        form.accept()
        return redirect("users")


# ====================================================================
# /users/<int:id>/delete
# ====================================================================

def delete(request, uid):
    d = init_render_dict(request)

    if request.method != "POST":
        d["confirm_form"] = {
            "title": "Delete user",
            "text": f"Are you sure that you want to delete this user ({uid})?",
            "return_url": "/users"
        }
        return render(request, "confirm_form.html", d)

    if not d["user"]["is_superuser"] and not d["user"].get("is_deptadmin"):
        raise PermissionDenied

    if d["user"].get("is_deptadmin") and not has_perm_deptadmin(request, uid):
        raise PermissionDenied

    form = UserActionForm({"user_id": uid})
    if form.is_valid():
        form.delete()
        return redirect("users")


# ====================================================================
# /users/<int:id>/activate
# ====================================================================

def activate(request, uid):
    if request.method != "POST":
        raise PermissionDenied

    d = init_render_dict(request)

    if not d["user"]["is_superuser"] and not d["user"].get("is_deptadmin"):
        raise PermissionDenied

    if d["user"].get("is_deptadmin") and not has_perm_deptadmin(request, uid):
        raise PermissionDenied

    form = UserActionForm({"user_id": uid})
    if form.is_valid():
        form.activate()
        return redirect("users")


# ====================================================================
# /users/<int:id>/deactivate
# ====================================================================

def deactivate(request, uid):
    if request.method != "POST":
        raise PermissionDenied

    d = init_render_dict(request)

    if not d["user"]["is_superuser"] and not d["user"].get("is_deptadmin"):
        raise PermissionDenied

    if d["user"].get("is_deptadmin") and not has_perm_deptadmin(request, uid):
        raise PermissionDenied

    form = UserActionForm({"user_id": uid})
    if form.is_valid():
        form.deactivate()
        return redirect("users")


# ====================================================================
# /users/<int:id>/classes/signup : Signup students to classes
# ====================================================================

def classes_signup(request, uid):
    d = init_render_dict(request)

    if request.user.id != uid or not d["user"].get("is_student"):
        raise PermissionDenied

    student = Student.objects.get(user=request.user)
    department = DepartmentStudents.objects.get(user_id=request.user).dept_id

    if department.state != States.SIGNUP:
        return render(request, "student_teaching_signup.html", d)

    if request.method == "POST":
        form = StudentClassSignupForm(student, request.POST)
        if form.is_valid():
            form.save()
    else:
        form = StudentClassSignupForm(student)

    d = init_render_dict(request)
    d["base_form"] = {
        "form": form,
        "title": "Class signup",
        "submit_value": "Save"
    }
    return render(request, "base_form.html", d)


# ====================================================================
# /users/<int:id>/grades
# ====================================================================

def grades(request, uid):
    if not request.user.is_authenticated or not request.user.is_student:
        raise PermissionDenied

    d = init_render_dict(request)
    d["classes"] = {}

    signups = ClassSignup.objects.filter(
        student__user=request.user
    ).order_by("-teaching__year")
    for i in signups:
        acc = d["classes"].get(i.teaching.class_id.name, [])
        acc.append(i)
        d["classes"][i.teaching.class_id.name] = acc

    return render(request, "student_grades.html", d)


# ====================================================================
# Signup
# ====================================================================

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
