from django import forms
from django.core.exceptions import ValidationError

from classes.models import Teaching, ClassSignup

from mainpage.models import States, Department


# ====================================================================
# Fields
# ====================================================================

class DepartmentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


# ====================================================================
# Forms
# ====================================================================

class DepartmentAddForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea()
        }
        help_texts = {
            "name": "Must be unique"
        }


class DepartmentStateForm(forms.ModelForm):

    def __init__(self, department, *args, **kwargs):
        super(DepartmentStateForm, self).__init__(*args, **kwargs)
        self.department = department
        self.fields["state"] = forms.ChoiceField(
            choices=States.choices, required=True
        )
        self.initial["state"] = self.department.state

    class Meta:
        model = Department
        fields = ["year", "semester", "state"]

    def clean(self):
        cleaned_data = super().clean()

        current_state = self.department.state
        state = cleaned_data["state"]
        semester = cleaned_data["semester"]
        year = cleaned_data["year"]

        # Check if the state transition is valid
        if current_state == States.SETUP:
            if not (state == current_state or state == States.SIGNUP):
                raise ValidationError(
                    "Cannot go from %(current)s state to %(new)s",
                    code="state",
                    params={"current": current_state, "new": state}
                )
        elif current_state == States.SIGNUP:
            if not (state == current_state or state == States.MARK):
                raise ValidationError(
                    "Cannot go from %(current)s state to %(new)s",
                    code="state",
                    params={"current": current_state, "new": state}
                )
        elif current_state == States.MARK:
            if not (state == current_state or state == States.SETUP):
                raise ValidationError(
                    "Cannot go from %(current)s state to %(new)s",
                    code="state",
                    params={"current": current_state, "new": state}
                )

        try:
            int(year)
        except ValueError:
            raise ValidationError("Please provide a valid year", code="year")

        # State: SETUP -> SIGNUP. Ensure that the grade weights are set.
        if state == States.SIGNUP:
            acc = []
            for i in Teaching.objects.filter(year=year, semester=semester):
                if i.theory_weight is None or i.lab_weight is None:
                    acc.append(i.class_id.name)
            if acc:
                raise ValidationError(
                    ("No theory or lab weight has been set for the following"
                     " classes: %(classes)s"), code="weight_error",
                    params={"classes": ", ".join(acc)})

        # State: MARK -> SETUP. Ensure that all signups are graded.
        if current_state == States.MARK and state == States.SIGNUP:
            acc = []
            for i in Teaching.objects.filter(year=year, semester=semester):
                for j in ClassSignup.objects.filter(teaching=i):
                    if not j.theory_mark or not j.lab_mark:
                        acc.append(
                            f"{j.student.registry_id} ({i.class_id.name})")
            if acc:
                raise ValidationError(
                    ("No theory or lab mark has been set for the following"
                     " students: %(st)s"), code="mark_error",
                    params={"st": ", ".join(acc)})

        return cleaned_data
