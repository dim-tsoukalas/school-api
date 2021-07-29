from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db import models


class EmailUserManager(BaseUserManager):

    def _create_user(self, email, password, **kwargs):
        if not email:
            raise ValueError(_("Users must provide an email address"))
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **kwargs):
        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)
        return self._create_user(email, password, **kwargs)

    def create_superuser(self, email, password, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)

        if kwargs.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if kwargs.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email_address"), max_length=255, unique=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    is_staff = models.BooleanField(_('active'), default=False)
    is_active = models.BooleanField(_('active'), default=True)

    objects = EmailUserManager()

    # is_superuser provided by PermissionsMixin
    is_deptadmin = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)


class Deptadmin(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True)
    department = models.ForeignKey(
        "mainpage.Department", on_delete=models.CASCADE)


class Teacher(models.Model):

    class TeacherRanks(models.TextChoices):
        ASSISTANT = "assistant", _("Assistant Professor")  # epikouros
        ASSOCIATE = "associate", _("Associate Professor")  # anaplirwtis
        PROFESSOR = "professor", _("Professor")  # kathigitis

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    rank = models.CharField(max_length=15, choices=TeacherRanks.choices)


class Student(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True)
    registry_id = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    admission_year = models.CharField(max_length=4)
