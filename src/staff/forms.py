from django import forms
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from mainpage.models import Department


"""
class DepartmentAdd(forms.Form):
    name = forms.CharField(
        label=_("Department Name"),
        max_length=Department.NAME_LENGTH,
        widget=forms.TextInput(attrs={
            'autofocus': False,
            "placeholder": _("Department Name")
        })
    )
"""


class DepartmentAddForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name"]

    def save(self):
        dept = super().save(commit=False)
        dept.save()
        return dept
