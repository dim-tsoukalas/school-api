from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from classes.models import Classes, PrerequisiteClasses, Teaching, ClassSignup

from .models import User, Student, Teacher, Deptadmin
from mainpage.models import Department, DepartmentStudents, DepartmentTeachers
from mainpage.forms import DepartmentChoiceField

import datetime


PASSING_MARK = 5


# ====================================================================
# Fields
# ====================================================================

class TeacherChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.first_name} {obj.last_name} ({obj.user.email})"


# ====================================================================
# Forms
# ====================================================================

# General ============================================================

class SigninForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        max_length=User.EMAIL_LENGTH,
        widget=forms.EmailInput(attrs={
            "autofocus": False, "placeholder": "Email"
        }),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "current-password", "placeholder": "Password"
        }),
    )

    error_messages = {
        "invalid_login": _("Incorrect email or password."),
        "disabled": _("Please wait for your account to be enabled."),
    }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user_cache = authenticate(username=email, password=password)
            if self.user_cache is None:
                raise ValidationError(
                    self.error_messages["invalid_login"], code="invalid_login"
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return cleaned_data

    def get_user(self):
        return self.user_cache

    def confirm_login_allowed(self, user):
        if not user.is_accepted:
            raise ValidationError(
                self.error_messages["disabled"],
                code="disabled",
            )


class UserActionForm(forms.Form):
    user_id = forms.IntegerField(required=True)

    def accept(self):
        user_id = self.cleaned_data.get("user_id")
        user = User.objects.get(id=user_id)
        user.is_accepted = True
        user.save()

    def delete(self):
        user_id = self.cleaned_data.get("user_id")
        User.objects.filter(id=user_id).delete()

    def activate(self):
        user_id = self.cleaned_data.get("user_id")
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()

    def deactivate(self):
        user_id = self.cleaned_data.get("user_id")
        user = User.objects.get(id=user_id)
        user.is_active = False
        user.save()


# Student ============================================================

class StudentSignupForm(UserCreationForm):
    department = DepartmentChoiceField(
        queryset=Department.objects.all(),
        required=True
    )
    email = forms.EmailField(
        max_length=254, help_text="Required. Enter a valid email address."
    )
    first_name = forms.CharField(max_length=200, required=True)
    last_name = forms.CharField(max_length=200, required=True)
    registry_id = forms.CharField(max_length=100, required=True)
    admission_year = forms.IntegerField(
        min_value=2000, max_value=datetime.datetime.now().year, required=True
    )

    error_messages = {
        "registry_id_exists": _("A student with this registry id already"
                                " exists."),
    }

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["department", "first_name", "last_name", "registry_id",
                  "admission_year", "email", "password1", "password2"]

    def clean(self):
        cleaned_data = super().clean()
        reg_id = cleaned_data.get("registry_id")
        if Student.objects.filter(registry_id=reg_id):
            raise ValidationError(
                self.error_messages["registry_id_exists"],
                code="registry_id_exists"
            )
        return cleaned_data

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_student = True
        user.save()
        student = Student.objects.create(user=user)
        student.registry_id = self.cleaned_data.get("registry_id")
        student.first_name = self.cleaned_data.get("first_name")
        student.last_name = self.cleaned_data.get("last_name")
        student.admission_year = self.cleaned_data.get("admission_year")
        student.save()
        DepartmentStudents.objects.create(
            dept_id=self.cleaned_data.get("department"),
            user_id=user
        )
        return user


class StudentUpdateForm(forms.ModelForm):
    department = DepartmentChoiceField(
        queryset=Department.objects.all(),
        required=True
    )
    first_name = forms.CharField(max_length=200, required=True)
    last_name = forms.CharField(max_length=200, required=True)
    registry_id = forms.CharField(max_length=100, required=True)
    admission_year = forms.IntegerField(
        min_value=2000, max_value=datetime.datetime.now().year, required=True
    )

    error_messages = {
        "email_exists": _("This email is used by another user."),
        "registry_id_exists": _("A student with this registry id already"
                                " exists."),
    }

    class Meta:
        model = User
        fields = ["department", "first_name", "last_name", "registry_id",
                  "admission_year", "email"]

    def clean(self):
        cleaned_data = super().clean()
        """
        email = cleaned_data.get("email")
        exists = User.objects.filter(email=email)
        if exists and not exists[0].id == cleaned_data.get("user_id"):
            raise ValidationError(
                self.error_messages["email_exists"],
                code="email_exists"
            )
        """
        reg_id = cleaned_data.get("registry_id")
        exists = Student.objects.filter(registry_id=reg_id)
        if exists and not exists[0].user.email == cleaned_data.get("email"):
            raise ValidationError(
                self.error_messages["registry_id_exists"],
                code="registry_id_exists"
            )

        return cleaned_data

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.save()
        student = Student.objects.get(user=user)
        student.first_name = self.cleaned_data.get("first_name")
        student.last_name = self.cleaned_data.get("last_name")
        student.registry_id = self.cleaned_data.get("registry_id")
        student.admission_year = self.cleaned_data.get("admission_year")
        student.save()
        dept = DepartmentStudents.objects.get(user_id=user)
        dept.dept_id = self.cleaned_data.get("department")
        dept.save()
        return user


class StudentClassSignupForm(forms.Form):

    def __init__(self, student_obj, *args, **kwargs):
        super(StudentClassSignupForm, self).__init__(*args, **kwargs)
        self.student_obj = student_obj

        self.year = Teaching.objects.aggregate(Max("year"))["year__max"]
        self.semester = Teaching.objects.filter(year=self.year).aggregate(
            Max("semester"))["semester__max"]

        # Classes for which the student has already signed up for.
        initial = ClassSignup.objects.filter(
            student=student_obj,
            teaching__year=self.year,
            teaching__semester=self.semester
        ).values_list("teaching__class_id__id", flat=True)

        self.initial["classes"] = list(initial)

        self.fields["classes"] = forms.MultipleChoiceField(
            label="",
            required=False,
            choices=self._get_available_signup_classes(),
            widget=forms.CheckboxSelectMultiple()
        )

    def _get_available_signup_classes(self):
        teachings = Teaching.objects.filter(
            year=self.year, semester=self.semester
        )
        acc = []
        for teaching in teachings:
            # Skip passed class.
            passed = ClassSignup.objects.filter(
                student=self.student_obj, final_mark__gte=PASSING_MARK,
                teaching=teaching
            ).exists()
            if passed:
                continue

            # Skip the class if there are prerequisite classes that the student
            # has not passed.
            if self._has_passed_prerequisite_classes(teaching.class_id):
                class_obj = teaching.class_id
                acc.append((class_obj.id, class_obj.name))

        return acc

    def _has_passed_prerequisite_classes(self, class_obj):
        prerequisites = PrerequisiteClasses.objects.filter(
            class_id=class_obj
        )
        for prerequisite in prerequisites:
            teachings = Teaching.objects.filter(
                class_id=prerequisite.prerequisite_id
            )
            passed = False
            for teaching in teachings:
                passed = ClassSignup.objects.filter(
                    student=self.student_obj, final_mark__gte=PASSING_MARK,
                    teaching=teaching
                ).exists()
                if passed:
                    break
            if not passed:
                return False

        return True

    def save(self):
        self._delete_old_signup()

        for i in self.cleaned_data["classes"]:
            class_obj = Classes.objects.get(id=i)
            teaching = Teaching.objects.get(
                class_id=class_obj, year=self.year, semester=self.semester)
            ClassSignup.objects.create(
                teaching=teaching, student=self.student_obj)

    def _delete_old_signup(self):
        ClassSignup.objects.filter(
            student=self.student_obj,
            teaching__year=self.year,
            teaching__semester=self.semester
        ).delete()


# Teacher ============================================================

class TeacherSignupForm(UserCreationForm):
    department = DepartmentChoiceField(
        queryset=Department.objects.all(),
        required=True
    )
    email = forms.EmailField(
        max_length=255, help_text="Required. Enter a valid email address."
    )
    first_name = forms.CharField(max_length=200, required=True)
    last_name = forms.CharField(max_length=200, required=True)
    rank = forms.ChoiceField(
        choices=Teacher.TeacherRanks.choices, required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["department", "first_name", "last_name", "rank", "email",
                  "password1", "password2"]

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_teacher = True
        user.save()
        teacher = Teacher.objects.create(user=user)
        teacher.first_name = self.cleaned_data.get("first_name")
        teacher.last_name = self.cleaned_data.get("last_name")
        teacher.rank = self.cleaned_data.get("rank")
        teacher.save()
        DepartmentTeachers.objects.create(
            dept_id=self.cleaned_data.get("department"),
            user_id=user
        )
        return user


class TeacherUpdateForm(forms.ModelForm):
    department = DepartmentChoiceField(
        queryset=Department.objects.all(),
        required=True
    )
    first_name = forms.CharField(max_length=200, required=True)
    last_name = forms.CharField(max_length=200, required=True)
    rank = forms.ChoiceField(
        choices=Teacher.TeacherRanks.choices, required=True
    )

    error_messages = {
        "email_exists": _("This email is used by another user.")
    }

    class Meta:
        model = User
        fields = ["department", "first_name", "last_name", "rank", "email"]

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.save()
        teacher = Teacher.objects.get(user=user)
        teacher.first_name = self.cleaned_data.get("first_name")
        teacher.last_name = self.cleaned_data.get("last_name")
        teacher.rank = self.cleaned_data.get("rank")
        teacher.save()
        dept = DepartmentTeachers.objects.get(user_id=user)
        dept.dept_id = self.cleaned_data.get("department")
        dept.save()
        return user


# Deptadmin ===============================================================

class DeptadminSignupForm(UserCreationForm):
    department = DepartmentChoiceField(
        queryset=Department.objects.all(),
        required=True
    )
    email = forms.EmailField(
        max_length=255, help_text="Required. Enter a valid email address."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["department", "email", "password1", "password2"]

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_deptadmin = True
        user.is_staff = True
        user.save()
        deptadmin = Deptadmin.objects.create(
            user=user, department=self.cleaned_data.get("department")
        )
        deptadmin.save()
        return user


class DeptadminUpdateForm(forms.ModelForm):
    department = DepartmentChoiceField(
        queryset=Department.objects.all(),
        required=True
    )

    error_messages = {
        "email_exists": _("This email is used by another user.")
    }

    class Meta:
        model = User
        fields = ["department", "email"]

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.save()
        deptadmin = Deptadmin.objects.get(user=user)
        deptadmin.department = self.cleaned_data.get("department")
        deptadmin.save()
        return user
