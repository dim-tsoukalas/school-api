from django import forms

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
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea()
        }
