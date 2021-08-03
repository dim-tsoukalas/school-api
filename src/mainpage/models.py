from django.db import models


class Department(models.Model):
    NAME_LENGTH = 200
    name = models.CharField(max_length=NAME_LENGTH)


class DepartmentStudents(models.Model):
    dept_id = models.ForeignKey("mainpage.Department", on_delete=models.CASCADE)
    student_id = models.ForeignKey("users.User", on_delete=models.CASCADE)


class DepartmentTeachers(models.Model):
    dept_id = models.ForeignKey("mainpage.Department", on_delete=models.CASCADE)
    teacher_id = models.ForeignKey("users.User", on_delete=models.CASCADE)
