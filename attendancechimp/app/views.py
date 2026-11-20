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
                     Lecture, QRCodeUpload, getUploadsForCourse)

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


def new_course(request):
    return render(request, "app/new_course.html")


def new_lecture(request):
    return render(request, "app/new_lecture.html")


def new_qr_upload(request):
    return render(request, "app/new_qr_upload.html")


@csrf_exempt
def createCourse(request):
    if request.method != "POST":
        return HttpResponse("Only POST", status=405)

    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    try:
        instructor = InstructorProfile.objects.get(user=request.user)
    except InstructorProfile.DoesNotExist:
        return HttpResponse("Not a professor", status=401)

    course_name = (request.POST.get("course-name") or "")
    if not course_name:
        return HttpResponseBadRequest("Missing course-name.")

    try:
        start_time = datetime.strptime(request.POST.get("start-time", ""), "%H:%M").time()
        end_time = datetime.strptime(request.POST.get("end-time", ""), "%H:%M").time()
    except:
        return HttpResponseBadRequest("Needs to be HH:MM.")

    if Course.objects.filter(course_name=course_name).exists():
        return HttpResponseBadRequest("Course already exists.")

    Course.objects.create(
        course_name=course_name,
        instructor=instructor,
        monday=bool(request.POST.get("day-mon")),
        tuesday=bool(request.POST.get("day-tue")),
        wednesday=bool(request.POST.get("day-wed")),
        thursday=bool(request.POST.get("day-thu")),
        friday=bool(request.POST.get("day-fri")),
        start_time=start_time,
        end_time=end_time,
    )

    return HttpResponse("Good", status=200)

@csrf_exempt
def createLecture(request):
    if request.method != "POST":
        return HttpResponse("Only POST", status=405)

    if not request.user.is_authenticated:
        return HttpResponse("Please log in", status=401)
    if not InstructorProfile.objects.filter(user=request.user).exists():
        return HttpResponse("Not a professor", status=401)

    choice = request.POST.get("choice", "")
    course = Course.objects.filter(course_name=choice).first()
    if course is None:
        return HttpResponse("Course Does not Exist", status=404)

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
        return HttpResponse("You need to be logged in", status=401)

    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        return HttpResponse("Not a student", status=401)

    photo = request.FILES.get("imageUpload")
    if photo is None:
        return HttpResponseBadRequest("No Photo")

    QRCodeUpload.objects.create(
        student=student,
        photo=photo,
    )



    return HttpResponse("Good", status=200)


def dumpUploads(request):

    if request.method != "GET":
        return HttpResponse("Only GET")

    if not request.user.is_authenticated:
        return HttpResponse("Need to be logged in", status=401)
    if not InstructorProfile.objects.filter(user=request.user).exists():
        return HttpResponse("Not a professor", status=401)

    data = [
        {
            "username": upload.student.user.username,
            "upload_time": upload.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for upload in QRCodeUpload.objects.all()
    ]
    return JsonResponse(data, safe=False)

# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------

def getUploads(request):
    if request.method != "GET":
        return HttpResponse("Cannt do GET", status=405)

    if not request.user.is_authenticated:
            return HttpResponse("You need to be logged in", status=401)
    if not InstructorProfile.objects.filter(user=request.user).exists():
            return HttpResponse("Not a professor", status=401)

    course = (request.GET.get("course") or "")
    if not course:
        return JsonResponse({"error": "Missing course parameter"}, status=400)

    uploads = getUploadsForCourse(course)

    data = [
        {
            "username": upload.student.user.username,
            "upload_time": upload.uploaded_at.astimezone(CDT).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for upload in uploads
    ]
    return JsonResponse(data, safe=False)



