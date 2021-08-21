"""class_manager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

import users.views
import mainpage.views
import staff.views
import classes.views

urlpatterns = [
    path("", mainpage.views.home, name="home"),
    path("signin", users.views.signin, name="signin"),
    path("signout", users.views.signout, name="signout"),
    path("signup", users.views.signup, name="signup"),
    path("signup/student", users.views.signup_student, name="signup_student"),
    path("signup/teacher", users.views.signup_teacher, name="signup_teacher"),
    # Users
    path("users", users.views.users, name="users"),
    path("users/<int:uid>", users.views.user),
    path("users/<int:uid>/update", users.views.user_update),
    path("users/<int:uid>/classes/signup", users.views.classes_signup),
    path("users/<int:uid>/grades", users.views.grades),
    # Superuser
    path("superuser", staff.views.superuser, name="superuser"),
    path("superuser/departments", staff.views.superuser_departments,
         name="superuser_departments"),
    path("superuser/departments/add", staff.views.superuser_departments_add,
         name="superuser_departments_add"),
    # Departments
    path("departments", mainpage.views.departments, name="departments"),
    path("departments/insert", mainpage.views.departments_insert),
    path("departments/<int:dept_id>/update",
         mainpage.views.departments_update),
    path("departments/<int:dept_id>/delete",
         mainpage.views.departments_delete),
    # Classes
    path("departments/<int:dept_id>/classes",
         classes.views.classes, name="classes"),
    path("departments/<int:dept_id>/classes/<str:class_public_id>/delete",
         classes.views.delete),
    path("departments/<int:dept_id>/classes/insert", classes.views.insert,
         name="classes/insert"),
    path("departments/<int:dept_id>/classes/<str:class_public_id>",
         classes.views.details, name="class"),
    path("departments/<int:dept_id>/classes/<str:class_public_id>/info/update",
         classes.views.info_update),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/prerequisites/insert"),
         classes.views.prerequisites_insert),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/prerequisites/<int:req_id>/delete"),
         classes.views.prerequisites_delete),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/insert"),
         classes.views.teaching_insert),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/<int:teaching_id>/update"),
         classes.views.teaching_update),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/<int:teaching_id>/delete"),
         classes.views.teaching_delete),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/<int:teaching_id>/grades"),
         classes.views.grades, name="grades"),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/<int:teaching_id>/grades/upload"),
         classes.views.grades_upload),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/<int:teaching_id>/grades/apply_previous"),
         classes.views.grades_apply_previous),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/<int:teaching_id>/grades/finalize"),
         classes.views.grades_finalize),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/<int:teaching_id>/export/grades"),
         classes.views.export_grades),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/<int:teaching_id>/export/signups"),
         classes.views.export_signups),
    path(("departments/<int:dept_id>/classes/<str:class_public_id>"
          "/teaching/<int:teaching_id>/grades/<int:grade_id>/update"),
         classes.views.grade_update),
    path("users/<int:user_id>/classes", classes.views.user_classes)
]
