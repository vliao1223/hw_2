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

from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
                     Lecture, QRCodeUpload, is_instructor, is_student,
                     getUploadsForCourse)

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

meeting_days_options = [
    ("day-mon", "M"),
    ("day-tue", "Tu"),
    ("day-wed", "W"),
    ("day-thu", "Th"),
    ("day-fri", "F"),
]


@csrf_exempt
def createCourse(request):

    if request.method != "POST":
        return HttpResponse("Only POST")

    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    try:
        instructor = InstructorProfile.objects.get(user=request.user)
    except InstructorProfile.DoesNotExist:
        return HttpResponse("Not a professor", status=401)

    course_name = request.POST.get("course-name")
    start_time = request.POST.get("start-time")
    end_time = request.POST.get("end-time")
    meeting_days = "".join(day_short for day, day_short in meeting_days_options if request.POST.get(day))

    Course.objects.create(
        course_name=course_name,
        instructor=instructor,
        meeting_days=meeting_days,
        start_time=start_time,
        end_time=end_time,
    )

    return HttpResponse("Good", status=200)

@csrf_exempt
def createLecture(request):
    if request.method != "POST":
        return HttpResponse("Only POST")

    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)
    if not InstructorProfile.objects.filter(user=request.user).exists():
        return HttpResponse("Unauthorized", status=401)

    choice = request.POST.get("choice")
    course = Course.objects.get(course_name=choice)


    Lecture.objects.create(
        course=course,
        date=datetime.now(CDT).date(),
    )

    return HttpResponse("Good", status=200)


@csrf_exempt
def createQRCodeUpload(request):

    if request.method != "POST":
        return HttpResponse("Only POST")

    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        return HttpResponse("Not a student", status=401)

    photo = request.FILES.get("imageUpload")


    QRCodeUpload.objects.create(
        student=student,
        photo=photo,
        uploaded_at=datetime.now(CDT)
    )

    return HttpResponse("Good", status=200)


def dumpUploads(request):

    if request.method != "GET":
        return HttpResponse("Only GET")

    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)
    if not InstructorProfile.objects.filter(user=request.user).exists():
        return HttpResponse("Unauthorized", status=401)

    data = [
        {
            "username": upload.student.user.username,
            "upload_time": upload.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for upload in QRCodeUpload.objects.select_related("student__user")
    ]
    return JsonResponse(data, safe=False)

# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



