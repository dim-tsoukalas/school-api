from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from mainpage.models import DepartmentTeachers

from users.models import Teacher
from users.forms import TeacherChoiceField

from .models import Classes, PrerequisiteClasses, Teaching


# ====================================================================
# Fields
# ====================================================================

class ClassChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


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


class ClassDescriptionForm(forms.ModelForm):
    class Meta:
        model = Classes
        fields = ["description"]
        widgets = {
            "description": forms.Textarea()
        }


# ====================================================================
# Prerequisite classes
# ====================================================================

class PrerequisiteClassForm(forms.ModelForm):

    def __init__(self, target_class, *args, **kwargs):
        super(PrerequisiteClassForm, self).__init__(*args, **kwargs)
        self.target_class = target_class
        self.fields["prerequisite_id"] = ClassChoiceField(
            queryset=Classes.objects.filter(
                department=target_class.department
            ).exclude(id=target_class.id),
            required=True,
            label=_("Prerequisite class")
        )

    class Meta:
        model = PrerequisiteClasses
        fields = ("prerequisite_id",)

    def clean(self):
        cleaned_data = self.cleaned_data
        exists = PrerequisiteClasses.objects.filter(
            class_id=self.target_class,
            prerequisite_id=cleaned_data.get("prerequisite_id")
        ).exists()

        if exists:
            raise ValidationError(
                _("This prerequisite class has already been added."),
                code="already_added")

        if self.target_class == cleaned_data.get("prerequisite_id"):
            raise ValidationError(
                _("A class cannot be a prerequisite of itself."),
                code="same_class")

        return cleaned_data


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

    def clean(self):
        cleaned_data = self.cleaned_data

        theory_weight = cleaned_data.get("theory_weight")
        lab_weight = cleaned_data.get("lab_weight")

        if theory_weight is not None:
            if theory_weight < 0 or theory_weight > 1:
                raise ValidationError(
                    _("The theory weight given is out of range."
                      " Make sure it is a value between 0 and 1 inclusive."),
                    code="weight_range_error")
            if lab_weight is None:
                lab_weight = Decimal(1) - theory_weight
                cleaned_data["lab_weight"] = lab_weight
            if theory_weight + lab_weight != 1:
                raise ValidationError(
                    _("Make sure the sum of the given weights is 1."),
                    code="weight_sum_error"
                )
        elif lab_weight is not None:
            if lab_weight < 0 or lab_weight > 1:
                raise ValidationError(
                    _("The lab weight given is out of range."
                      " Make sure it is a value between 0 and 1 inclusive."),
                    code="weight_range_error")
            if theory_weight is None:
                theory_weight = Decimal(1) - lab_weight
                cleaned_data["theory_weight"] = theory_weight
            if theory_weight + lab_weight != 1:
                raise ValidationError(
                    _("Make sure the sum of the given weights is 1."),
                    code="weight_sum_error"
                )

        return cleaned_data
