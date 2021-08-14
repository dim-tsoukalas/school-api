from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from mainpage.models import Department, DepartmentTeachers
from mainpage.forms import DepartmentChoiceField

from users.models import Teacher
from users.forms import TeacherChoiceField

from .models import Classes, Teaching


# ====================================================================
# Classes: class info
# ====================================================================

class ClassInsertForm(forms.ModelForm):

    def __init__(self, department, *args, **kwargs):
        super(ClassInsertForm, self).__init__(*args, **kwargs)
        self.department = department

    class Meta:
        model = Classes
        fields = ["public_id", "name", "description"]
        widgets = {
            "description": forms.Textarea()
        }

    def clean(self):
        cleaned_data = self.cleaned_data
        exists = Classes.objects.filter(
            name=cleaned_data["name"],
            department=self.department
        ).exists()

        if exists and not self._is_update_mode():
            raise ValidationError("Class with this name already exists.")

        return cleaned_data

    def _is_update_mode(self):
        return self.instance == Classes.objects.get(
            name=self.cleaned_data["name"],
            department=self.department
        )


# ====================================================================
# Teaching
# ====================================================================

class TeachingInsertForm(forms.ModelForm):
    """Must be initialized with `dept_id and `class_id'"""

    def __init__(self, dept_id, form_mode, *args, **kwargs):
        super(TeachingInsertForm, self).__init__(*args, **kwargs)

        if form_mode == "admin_insert" or form_mode == "admin_update":
            _users = DepartmentTeachers.objects.filter(
                dept_id=dept_id).values_list("user_id")

            self.fields["teacher"] = TeacherChoiceField(
                queryset=Teacher.objects.filter(user__in=_users),
                required=True
            )

        if form_mode == "admin_insert":
            self.fields.pop("theory_weight")
            self.fields.pop("lab_weight")
            self.fields.pop("theory_limit")
            self.fields.pop("lab_limit")
        elif form_mode == "teacher_update":
            self.fields.pop("year")
            self.fields.pop("semester")
            self.fields.pop("teacher")

    class Meta:
        model = Teaching
        fields = ["year", "semester", "teacher", "theory_weight",
                  "lab_weight", "theory_limit", "lab_limit"]
