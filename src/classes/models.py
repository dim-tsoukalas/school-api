from django.db import models

from mainpage.models import Semesters


class Classes(models.Model):
    PUBLIC_ID_LENGTH = 200
    NAME_LENGTH = 200
    DESCRIPTION_LENGTH = 512

    # Modifiable Id visible to the user. Different from class_id.
    public_id = models.CharField(max_length=PUBLIC_ID_LENGTH, unique=True)
    department = models.ForeignKey(
        "mainpage.Department", on_delete=models.CASCADE)
    name = models.CharField(max_length=NAME_LENGTH)
    description = models.CharField(max_length=DESCRIPTION_LENGTH, blank=True)

    class Meta:
        unique_together = ("department", "name")


class PrerequisiteClasses(models.Model):
    class_id = models.ForeignKey(
        Classes, related_name="prerequisite_id", on_delete=models.CASCADE
    )
    prerequisite_id = models.ForeignKey(
        Classes, related_name="class_id", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("class_id", "prerequisite_id")


class Teaching(models.Model):
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)
    year = models.CharField(max_length=4)

    semester = models.CharField(max_length=15, choices=Semesters.choices)
    teacher = models.ForeignKey("users.Teacher", on_delete=models.CASCADE)

    # Both of them should amount to 1.00. Both must be set.
    theory_weight = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True)
    lab_weight = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True)

    theory_limit = models.CharField(max_length=4, blank=True)
    lab_limit = models.CharField(max_length=4, blank=True)


class ClassSignup(models.Model):
    teaching = models.ForeignKey(Teaching, on_delete=models.CASCADE)
    student = models.ForeignKey("users.Student", on_delete=models.CASCADE)

    theory_mark = models.DecimalField(
        max_digits=5, decimal_places=2, null=True)
    lab_mark = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    final_mark = models.DecimalField(max_digits=5, decimal_places=2, null=True)
