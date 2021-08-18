from django import forms
from django.core.exceptions import ValidationError

from classes.models import Teaching

from mainpage.models import Department


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
        fields = ["name", "description", "state", "year", "semester"]
        widgets = {
            "description": forms.Textarea()
        }

    def clean(self):
        cleaned_data = self.cleaned_data

        semester = cleaned_data["semester"]
        year = cleaned_data["year"]
        try:
            int(year)
        except ValueError:
            raise ValidationError("Please provide a valid year", code="year")

        if cleaned_data["state"] == "signup":
            acc = []
            for i in Teaching.objects.filter(year=year, semester=semester):
                if not i.theory_weight or not i.lab_weight:
                    acc.append(i.class_id.name)
            if acc:
                raise ValidationError(
                    ("No theory or lab weight has been set for the following"
                     " classes: %(classes)s"), code="weight_error",
                    params={"classes": ", ".join(acc)})

        return cleaned_data
