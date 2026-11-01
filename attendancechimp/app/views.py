"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import datetime
import zoneinfo
import json
import io

from .models import (InstructorProfile, StudentProfile)

# from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
#                      Lecture, QRCodeUpload, is_instructor, is_student,
#                      getUploadsForCourse)

CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

def index(request):
    """Render the home page (index.html)."""
    user = request.user
    context = {
        "username": user.get_username() if user.is_authenticated else None,
        "time": datetime.now(CDT).strftime("%H:%M"),
    }
    return render(request, 'app/index.html', context)

def time_view(request):
    return HttpResponse(datetime.now(CDT).strftime("%H:%M"))

def sum_view(request):
    n1 = float(request.GET.get("n1"))
    n2 = float(request.GET.get("n2"))
    sum = n1 + n2

    return HttpResponse(f"<p>{sum}</p>")

# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------

def new(request):
    """Render the sign-up form."""
    if request.method != "GET":
        return HttpResponseForbidden("Only GET requests.")
    return render(request, "app/new.html")

@csrf_exempt
def createUser(request):
    """Create a User and login"""
    if request.method != "POST":
        return HttpResponseForbidden("Only POST requests.")

    email = request.POST.get("email")
    username = request.POST.get("user_name")
    password = request.POST.get("password")
    is_student = request.POST.get("is_student")

    if User.objects.filter(email=email).exists():
        return HttpResponseBadRequest("Email already exists.")

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    if is_student == "1":
        StudentProfile.objects.create(
            user=user,
            first_name="",
            last_name="",
            school_email=email,
        )
    else:
        InstructorProfile.objects.create(
            user=user,
            first_name="",
            last_name="",
            school_email=email,
            department="",
        )

    login(request, authenticate(request, username=username, password=password))

    return HttpResponse(f"Hello, {username}. You have successfully created your account!")

# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



