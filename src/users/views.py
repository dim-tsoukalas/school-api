from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect

from mainpage.models import DepartmentStudents, DepartmentTeachers

from classes.models import ClassSignup

from .models import User, Teacher, Student, Deptadmin
from .forms import (
    UserActionForm,
    StudentSignupForm, StudentUpdateForm, StudentClassSignupForm,
    TeacherSignupForm, TeacherUpdateForm,
    DeptadminSignupForm, DeptadminUpdateForm,
    SigninForm
)


# ====================================================================
# Helpers
# ====================================================================

def get_user_type(user):
    try:
        data = Student.objects.get(user=user)
        return "student", data
    except Student.DoesNotExist:
        pass

    try:
        data = Teacher.objects.get(user=user)
        return "teacher", data
    except Teacher.DoesNotExist:
        pass

    try:
        data = Deptadmin.objects.get(user=user)
        return "deptadmin", data
    except Deptadmin.DoesNotExist:
        pass


def get_user_dept_id(user, user_type):
    if user_type == "student":
        return DepartmentStudents.objects.get(user_id=user.id).dept_id

    if user_type == "teacher":
        return DepartmentTeachers.objects.get(user_id=user.id).dept_id

    if user_type == "deptadmin":
        return Deptadmin.objects.get(user_id=user.id).department.id


def make_user_data(user, type_data, user_type):
    if user_type == "student":
        return make_user_data_student(user, type_data)

    if user_type == "teacher":
        return make_user_data_teacher(user, type_data)

    if user_type == "deptadmin":
        return make_user_data_deptadmin(user, type_data)


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


def make_table_teachers(teachers):
    rows = []
    for teacher in teachers:
        rows.append(make_user_data_teacher(teacher.user, teacher))
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
    if request.method == "POST":
        return users_post(request)

    return users_get(request)


# GET ================================================================

def users_get(request):
    if request.GET.get("action") == "insert_student":
        return users_get_insert_student(request)

    if request.GET.get("action") == "insert_teacher":
        return users_get_insert_teacher(request)

    if request.GET.get("action") == "insert_deptadmin":
        return users_get_insert_deptadmin(request)

    if request.user.is_superuser:
        d = {
            "students": make_table_students(Student.objects.all()),
            "teachers": make_table_teachers(Teacher.objects.all()),
            "deptadmins": make_table_deptadmins(Deptadmin.objects.all())
        }
        return render(request, "users.html", d)
    elif request.user.is_deptadmin:
        pass
    else:
        raise PermissionDenied


def users_get_insert_student(request):
    if request.user.is_superuser:
        t_dict = {
            "mode": "student",
            "form": StudentSignupForm()
        }
        return render(request, "users_insert.html", t_dict)
    elif request.user.is_deptadmin:
        pass
    else:
        pass


def users_get_insert_teacher(request):
    if request.user.is_superuser:
        t_dict = {
            "mode": "teacher",
            "form": TeacherSignupForm()
        }
        return render(request, "users_insert.html", t_dict)
    elif request.user.is_deptadmin:
        pass
    else:
        pass


def users_get_insert_deptadmin(request):
    if request.user.is_superuser:
        t_dict = {
            "mode": "deptadmin",
            "form": DeptadminSignupForm()
        }
        return render(request, "users_insert.html", t_dict)

    raise PermissionDenied


# POST ===============================================================

def users_post(request):
    if request.POST.get("action") == "insert_student":
        return users_post_insert_student(request)

    if request.POST.get("action") == "insert_teacher":
        return users_post_insert_teacher(request)

    if request.POST.get("action") == "insert_deptadmin":
        return users_post_insert_deptadmin(request)


def users_post_insert_student(request):
    if request.user.is_superuser:
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_accepted = True
            user.save()
            return redirect("users")
        else:
            t_dict = {"mode": "student", "form": form}
            return render(request, "users_insert.html", t_dict)

    if request.user.is_deptadmin:
        pass

    raise PermissionDenied


def users_post_insert_teacher(request):
    if request.user.is_superuser:
        form = TeacherSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_accepted = True
            user.save()
            return redirect("users")
        else:
            t_dict = {"mode": "teacher", "form": form}
            return render(request, "users_insert.html", t_dict)

    if request.user.is_deptadmin:
        pass

    raise PermissionDenied


def users_post_insert_deptadmin(request):
    if request.user.is_superuser:
        form = DeptadminSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_accepted = True
            user.save()
            return redirect("users")
        else:
            t_dict = {"mode": "deptadmin", "form": form}
            return render(request, "users_insert.html", t_dict)

    raise PermissionDenied


# ====================================================================
# /users/<int:id> : Accessing a user
# ====================================================================

def user(request, uid=None):
    if request.method == "POST":
        return user_post(request)


# POST ===============================================================

def user_post(request):
    if request.POST["action"] == "accept":
        return user_post_accept(request)

    if request.POST["action"] == "delete":
        return user_post_delete(request)

    if request.POST["action"] == "activate":
        return user_post_activate(request)

    if request.POST["action"] == "deactivate":
        return user_post_deactivate(request)

    if request.POST["action"] == "update_student":
        return user_post_update_student(request)

    if request.POST["action"] == "update_teacher":
        return user_post_update_teacher(request)

    if request.POST["action"] == "update_deptadmin":
        return user_post_update_deptadmin(request)


def user_post_accept(request):
    form = UserActionForm(request.POST)
    if request.user.is_superuser:
        if form.is_valid():
            form.accept()
            return redirect("users")

    raise PermissionDenied()


def user_post_delete(request):
    form = UserActionForm(request.POST)
    if request.user.is_superuser:
        if form.is_valid():
            form.delete()
            return redirect("users")

    raise PermissionDenied()


def user_post_activate(request):
    form = UserActionForm(request.POST)
    if request.user.is_superuser:
        if form.is_valid():
            form.activate()
            return redirect("users")

    raise PermissionDenied()


def user_post_deactivate(request):
    form = UserActionForm(request.POST)
    if request.user.is_superuser:
        if form.is_valid():
            form.deactivate()
            return redirect("users")

    raise PermissionDenied()


def user_post_update_student(request):
    if request.user.is_superuser:
        form = StudentUpdateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users")
        else:
            t_dict = {"type": "student", "form": form}
            return render(request, "users_update.html", t_dict)

    raise PermissionDenied()


def user_post_update_teacher(request):
    if request.user.is_superuser:
        form = TeacherUpdateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users")
        else:
            t_dict = {"type": "teacher", "form": form}
            return render(request, "users_update.html", t_dict)

    raise PermissionDenied()


def user_post_update_deptadmin(request):
    if request.user.is_superuser:
        form = DeptadminUpdateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users")
        else:
            t_dict = {"type": "deptadmin", "form": form}
            return render(request, "users_update.html", t_dict)

    raise PermissionDenied()


# ====================================================================
# /users/<int:id>/update : Updating user info
# ====================================================================

def user_update(request, uid):
    if request.user.is_superuser:
        user = User.objects.get(id=uid)
        user_type, type_data = get_user_type(user)

        t_dict = make_user_data(user, type_data, user_type)
        t_dict["department"] = get_user_dept_id(user, user_type)

        if user_type == "student":
            t_dict["form"] = StudentUpdateForm(t_dict)
        elif user_type == "teacher":
            t_dict["form"] = TeacherUpdateForm(t_dict)
        elif user_type == "deptadmin":
            t_dict["form"] = DeptadminUpdateForm(t_dict)

        return render(request, "users_update.html", t_dict)
    elif request.user.is_deptadmin:
        pass
    else:
        pass


# ====================================================================
# /users/<int:id>/classes/signup : Signup students to classes
# ====================================================================

def classes_signup(request, uid):
    if request.user.id != uid:
        raise PermissionDenied

    if request.method == "POST":
        return classes_signup_post(request, uid)

    student = Student.objects.get(user=request.user)

    form = StudentClassSignupForm(student)

    t_dict = {
        "form": form,
        "t": {
            "title": "Class signup",
            "sumbit_value": "Save"
        }
    }
    return render(request, "base_form.html", t_dict)


def classes_signup_post(request, uid):
    student = Student.objects.get(user=request.user)

    form = StudentClassSignupForm(student, request.POST)

    if form.is_valid():
        form.save()

    t_dict = {
        "form": form,
        "t": {
            "title": "Class signup",
            "sumbit_value": "Save"
        }
    }
    return render(request, "base_form.html", t_dict)


# ====================================================================
# /users/<int:id>/grades
# ====================================================================

def grades(request, uid):
    if not request.user.is_authenticated or not request.user.is_student:
        raise PermissionDenied

    d = {"classes": {}}
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
