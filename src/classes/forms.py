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
    department = DepartmentChoiceField(
        queryset=Department.objects.all(),
        required=True
    )

    error_messages = {
        "public_id_exists": _("A class with this Id already exists."),
        "name_exists": _("A class with this name already exists."),
    }

    class Meta:
        model = Classes
        fields = ["department", "public_id", "name", "description"]
        widgets = {
            "description": forms.Textarea()
        }


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
