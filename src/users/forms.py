from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import User, Student, Teacher


# TODO: add department selection


class StudentSignupForm(UserCreationForm):
    email = forms.EmailField(
        max_length=255, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=200, required=True)
    last_name = forms.CharField(max_length=200, required=True)
    registry_id = forms.CharField(max_length=100, required=True)
    admission_year = forms.CharField(max_length=4, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["first_name", "last_name", "registry_id", "admission_year",
                  "email", "password1", "password2"]

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
        return user


class TeacherSignupForm(UserCreationForm):
    email = forms.EmailField(
        max_length=255, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=200, required=True)
    last_name = forms.CharField(max_length=200, required=True)
    rank = forms.ChoiceField(choices=Teacher.TeacherRanks.choices)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["first_name", "last_name", "rank", "email", "password1",
                  "password2"]

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
        return user


class SigninForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        max_length=User.EMAIL_LENGTH,
        widget=forms.EmailInput(attrs={
            'autofocus': False,
            "placeholder": "Email"
        })
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            "placeholder": "Password"
        })
    )

    error_messages = {
        'invalid_login': _("Incorrect email or password."),
        'inactive': _("This account is inactive."),
    }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if email and password:
            self.user_cache = authenticate(username=email, password=password)
            if self.user_cache is None:
                raise ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return cleaned_data

    def get_user(self):
        return self.user_cache

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )
