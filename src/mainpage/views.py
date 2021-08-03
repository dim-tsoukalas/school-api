from django.shortcuts import render

from users.forms import SigninForm


def home(request):
    r_dict = {"user": request.user}
    if not request.user.is_authenticated:
        r_dict["signin_form"] = SigninForm()

    return render(request, "mainpage.html", r_dict)
