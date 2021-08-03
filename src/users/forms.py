from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import User, Student, Teacher
from mainpage.models import Department, DepartmentStudents, DepartmentTeachers

import datetime


# ====================================================================
# Helpers
# ====================================================================

class DepartmentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


# ====================================================================
# Forms
# ====================================================================

class StudentSignupForm(UserCreationForm):
    department = DepartmentChoiceField(
        queryset=Department.objects.all(),
        required=True
    )
    email = forms.EmailField(
        max_length=255, help_text="Required. Enter a valid email address."
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
            student_id=user
        )
        return user


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
        user.is_student = True
        user.save()
        teacher = Teacher.objects.create(user=user)
        teacher.first_name = self.cleaned_data.get("first_name")
        teacher.last_name = self.cleaned_data.get("last_name")
        teacher.rank = self.cleaned_data.get("rank")
        teacher.save()
        DepartmentTeachers.objects.create(
            dept_id=self.cleaned_data.get("department"),
            teacher_id=user
        )
        return user


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
