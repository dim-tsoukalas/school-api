import csv
import io
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from mainpage.models import DepartmentTeachers

from users.models import Teacher, Student
from users.forms import TeacherChoiceField

from .models import Classes, PrerequisiteClasses, Teaching, ClassSignup


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


# ====================================================================
# Grades
# ====================================================================

def apply_grade(signup, theory, lab):
    signup.theory_mark = theory
    signup.lab_mark = lab
    if theory >= 5 and lab >= 5:
        signup.final_mark = (
            (signup.lab_mark * signup.teaching.lab_weight)
            + (signup.theory_mark * signup.teaching.theory_weight)
        )
    elif theory < lab:
        signup.final_mark = theory
    else:
        signup.final_mark = lab
    signup.save()


class GradeUpdateForm(forms.ModelForm):
    class Meta:
        model = ClassSignup
        fields = ["theory_mark", "lab_mark"]

    def save(self):
        signup = super().save(commit=False)
        apply_grade(signup, signup.theory_mark, signup.lab_mark)


class GradesCSVFileForm(forms.Form):
    def __init__(self, teaching, *args, **kwargs):
        self.teaching = teaching
        super(GradesCSVFileForm, self).__init__(*args, **kwargs)

        self.fields["file"] = forms.FileField(
            validators=[self._filesize, self._content_type,
                        self._data_validate]
        )

    def _filesize(self, f):
        if f.size > 2 * 1024 * 1024:  # 2 MiB filesize limit
            raise ValidationError(_("File too large. Size limit: 2 MiB"))

    def _content_type(self, f):
        if f.content_type != "text/csv":
            raise ValidationError(_("Please upload a CSV (text/csv) file."))

    def _data_validate(self, f):
        rows = csv.reader(
            io.StringIO(f.read().decode("utf-8"), newline=None)
        )
        rid_errors = []
        mark_errors = []
        row_errors = []
        next(rows)  # skip header
        for count, row in enumerate(rows):
            try:
                registry_id, theory_g, lab_g = row
            except ValueError:
                # Make it 1-indexed and include the skipped header.
                row_errors.append(str(count + 2))
                continue

            try:
                Decimal(theory_g)
                Decimal(lab_g)
            except InvalidOperation:
                mark_errors.append(registry_id)

            try:
                student = Student.objects.get(registry_id=registry_id)
            except Student.DoesNotExist:
                rid_errors.append(registry_id)
                continue

            exists = ClassSignup.objects.filter(
                    student=student, teaching=self.teaching
            ).exists()
            if not exists:
                rid_errors.append(registry_id)

        errors = []
        if rid_errors:
            errors.append(ValidationError(
                _("The following Ids do not exist or have not signed up for"
                  " this class: %(err)s"),
                params={"err": ", ".join(rid_errors)}))
        if mark_errors:
            errors.append(ValidationError(
                _("The grades for the following Ids are not valid decimals:"
                  " %(err)s"),
                params={"err": ", ".join(mark_errors)}))
        if row_errors:
            errors.append(ValidationError(
                _("The follwing rows are malformed: %(err)s"),
                params={"err": ", ".join(row_errors)}))

        if errors:
            raise ValidationError(errors)

    def handle(self, f):
        # Reset the cursor. Needed because _data_validate also reads the file.
        f.seek(0)
        rows = csv.reader(
            io.StringIO(f.read().decode("utf-8"), newline=None)
        )
        next(rows)  # skip header
        for row in rows:
            registry_id, theory_g, lab_g = row
            student = Student.objects.get(registry_id=registry_id)
            signup = ClassSignup.objects.get(
                student=student, teaching=self.teaching
            )
            apply_grade(signup, Decimal(theory_g), Decimal(lab_g))
