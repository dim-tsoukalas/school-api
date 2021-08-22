import io
import base64

import matplotlib.pyplot as plt
from matplotlib import numpy as np

from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.db.models import Max

from mainpage.models import Semesters
from classes.models import Teaching, ClassSignup


PASSING_MARK = 5


# ====================================================================
# Helpers: Text stats
# ====================================================================

def num_total_classes_passed(user_id):
    passed = 0
    failed = 0
    signups = ClassSignup.objects.filter(
        student__user__id=user_id, locked=True
    ).only("final_mark")
    for signup in signups:
        if signup.final_mark >= PASSING_MARK:
            passed += 1
        else:
            failed += 1
    return passed, failed


def num_total_students_passed(user_id):
    passed = 0
    failed = 0
    signups = ClassSignup.objects.filter(
        teaching__teacher__user__id=user_id,
        locked=True
    ).only("final_mark")
    for signup in signups:
        if signup.final_mark >= PASSING_MARK:
            passed += 1
        else:
            failed += 1
    return passed, failed


# ====================================================================
# Helpers: Graphs
# ====================================================================

def pie_classes_passed(user_id, year, semester):
    signups = ClassSignup.objects.filter(
        student__user__id=user_id,
        teaching__year=year,
        teaching__semester=semester,
        locked=True
    ).only("final_mark")
    passed = 0
    failed = 0
    for signup in signups:
        if signup.final_mark >= PASSING_MARK:
            passed += 1
        else:
            failed += 1

    passed = passed / (passed + failed) * 100
    failed = 100 - passed
    labels = "Passed", "Failed"
    sizes = [passed, failed]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.1f%%")
    ax.axis("equal")

    output = io.StringIO()
    fig.savefig(output, format="svg")
    output.seek(0)
    return base64.b64encode(output.getvalue().encode()).decode()


def bar_classes_assigned_per_year(user_id):
    teachings = Teaching.objects.filter(
        teacher__user__id=user_id
    ).only("year").order_by("year")
    years = {}
    for teaching in teachings:
        years[teaching.year] = years.get(teaching.year, 0) + 1

    fig, ax = plt.subplots()
    x = np.arange(len(years.keys()))
    rects = ax.bar(x, years.values(), width=0.3)
    ax.set_xlabel("Years")
    ax.set_ylabel("Classes")
    ax.set_title("Number of assigned classes per year")
    ax.set_xticks(x)
    ax.set_xticklabels(years.keys())
    # Y axis: set integer ticks
    ax.yaxis.get_major_locator().set_params(integer=True)
    # ax.bar_label(rects)
    fig.tight_layout()

    output = io.StringIO()
    fig.savefig(output, format="svg")
    output.seek(0)
    return base64.b64encode(output.getvalue().encode()).decode()


def pie_students_passed(teaching):
    signups = ClassSignup.objects.filter(
        teaching=teaching
    ).only("final_mark", "locked")
    passed = 0
    failed = 0
    pending = 0
    for signup in signups:
        if not signup.locked:
            pending += 1
        elif signup.final_mark >= PASSING_MARK:
            passed += 1
        else:
            failed += 1

    if (passed + failed + pending) == 0:
        labels = ["No signups yet"]
        colors = ["gray"]
        sizes = [100]
    elif pending == 0:
        labels = f"Passed ({passed})", f"Failed ({failed})"
        colors = "green", "orange"
        passed = passed / (passed + failed) * 100
        failed = 100 - passed
        sizes = [passed, failed]
    else:
        labels = (f"Passed ({passed})", f"Failed ({failed})",
                  f"Pending ({pending})")
        colors = ("green", "orange", "gray")
        passed = passed / (passed + failed + pending) * 100
        failed = failed / (passed + failed + pending) * 100
        pending = 100 - passed + failed
        sizes = [passed, failed, pending]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors)
    ax.set_title(f"{teaching.class_id.name}"
                 f" ({teaching.year} - {Semesters(teaching.semester).label})")
    ax.axis("equal")
    ax.legend()

    output = io.StringIO()
    fig.savefig(output, format="svg")
    output.seek(0)
    return base64.b64encode(output.getvalue().encode()).decode()


# ====================================================================
# /users/<int:id>/stats
# ====================================================================

def stats(request, uid):
    if not request.user.is_authenticated:
        raise PermissionDenied
    elif request.user.is_student:
        return stats_student(request, uid)
    elif request.user.is_teacher:
        return stats_teacher(request, uid)
    else:
        raise PermissionDenied


def stats_student(request, uid):
    opt_query = ClassSignup.objects.filter(
        student__user__id=uid
    ).select_related(
        "teaching"
    ).only(
        "teaching__year", "teaching__semester"
    ).distinct()
    graphs = {}
    for opt in opt_query:
        year = opt.teaching.year
        semester = opt.teaching.semester
        graphs[f"{year} {semester}"] = pie_classes_passed(uid, year, semester)

    passed, failed = num_total_classes_passed(uid)
    return render(request, "stats_students.html", {
        "pie": graphs,
        "total": failed + passed,
        "total_passed": passed,
        "total_failed": failed
    })


def stats_teacher(request, uid):
    graphs = {
        "bar_classes": bar_classes_assigned_per_year(uid)
    }

    year = request.GET.get("students_graphs_year")
    if not year:
        year = Teaching.objects.filter(
            teacher__user__id=uid).aggregate(Max("year"))["year__max"]

    pies_students = []
    teachings = Teaching.objects.filter(teacher__user__id=uid, year=year)
    for teaching in teachings:
        pies_students.append(pie_students_passed(teaching))

    graphs["pies_students"] = pies_students

    passed, failed = num_total_students_passed(uid)

    graphs["text_students"] = {
        "total": passed + failed,
        "passed": passed,
        "failed": failed
    }

    pies_students_years = []
    teachings = Teaching.objects.filter(
        teacher__user__id=uid).only("year").order_by("year")
    for teaching in teachings:
        if teaching.year not in pies_students_years:
            pies_students_years.append(teaching.year)

    graphs["pies_students_years"] = pies_students_years

    return render(request, "stats_teacher.html", graphs)
