from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import User, Student


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
