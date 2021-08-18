from django.db import models
from django.utils.translation import gettext_lazy as _


# Choices

class States(models.TextChoices):
    # In the SETUP state admins can add or delete classes, insert new teachings
    # and assign Teacher. Teachers can also add weights and limits for their
    # classes.
    SETUP = "setup", _("Classes setup")
    # In the SINGUP state classes and teachings are finalized and students can
    # signup to the classes they are eligible for.
    SIGNUP = "signup", _("Class signups")
    # In the MARK state class signups have been finalized and teachers must
    # insert the marks.
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
    year = models.CharField(max_length=4)
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
