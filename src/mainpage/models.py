from django.db import models


class Department(models.Model):
    NAME_LENGTH = 200
    DESCRIPTION_LENGTH = 512

    name = models.CharField(max_length=NAME_LENGTH, unique=True)
    description = models.CharField(max_length=DESCRIPTION_LENGTH, blank=True)


class DepartmentStudents(models.Model):
    dept_id = models.ForeignKey(
        "mainpage.Department", on_delete=models.CASCADE)
    user_id = models.ForeignKey("users.User", on_delete=models.CASCADE)


class DepartmentTeachers(models.Model):
    dept_id = models.ForeignKey(
        "mainpage.Department", on_delete=models.CASCADE)
    user_id = models.ForeignKey("users.User", on_delete=models.CASCADE)
