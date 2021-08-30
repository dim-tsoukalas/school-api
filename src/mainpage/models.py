from django.db import models
from django.utils.translation import gettext_lazy as _


# Choices

class States(models.TextChoices):
    # In the SETUP state students are not allowed to signup to new teachings.
    SETUP = "setup", _("Classes setup")
    # In the SINGUP state students may signups to a new teaching.
    SIGNUP = "signup", _("Class signups")
    # In the MARK state teachers must input the grades of all the signed up
    # students.
    MARK = "mark", _("Class marks")


class Semesters(models.TextChoices):
    FIRST = "first", _("First Semester")  # xeimerino
    SECOND = "second", _("Second Semester")  # earino


# Models

class Department(models.Model):
    NAME_LENGTH = 200
    DESCRIPTION_LENGTH = 512

    name = models.CharField(max_length=NAME_LENGTH, unique=True)
    description = models.CharField(max_length=DESCRIPTION_LENGTH, blank=True)

    state = models.CharField(
        max_length=6, choices=States.choices, default=States.SETUP)
    year = models.CharField(max_length=4, blank=True)
    semester = models.CharField(
        max_length=15, choices=Semesters.choices, default=Semesters.FIRST)


class DepartmentStudents(models.Model):
    dept_id = models.ForeignKey(
        "mainpage.Department", on_delete=models.CASCADE)
    user_id = models.ForeignKey("users.User", on_delete=models.CASCADE)


class DepartmentTeachers(models.Model):
    dept_id = models.ForeignKey(
        "mainpage.Department", on_delete=models.CASCADE)
    user_id = models.ForeignKey("users.User", on_delete=models.CASCADE)
