"""
models.py — Data model for AttendanceChimp.

AttendanceChimp is an electronic class attendance tool.  Instructors create
courses and lectures; each lecture is assigned a random QR code.  Students
photograph the QR code and upload the image.  The system decodes the QR code,
matches it to a lecture, and records the attendance.

Entities
--------
- CourseProfile   : extends Django User → instructor-specific data
- StudentProfile  : extends Django User → student-specific data
- Course          : a course taught by one instructor
- Enrollment      : junction table linking students to courses
- Lecture         : a single class meeting (has a QR-code identifier)
- QRCodeUpload    : a student's uploaded QR-code photograph
"""

from django.db import models
from django.contrib.auth.models import User

import logging
import string
import random

import zoneinfo
import datetime
CDT = zoneinfo.ZoneInfo("America/Chicago")

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------
class StudentProfile(models.Model):
    """Stores profile information for students."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    school_email = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.student_id}"

class InstructorProfile(models.Model):
    """Stores profile information for instructors."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    instructor_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    school_email = models.CharField(max_length=50)
    department = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.instructor_id}"


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class Course(models.Model):
    """Stores information about courses."""
    course_name = models.CharField(max_length=50, unique=True)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.SET_NULL, null=True)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course_id}"


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class Enrollment(models.Model):
    """Junction table for Student and Course"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="pk_student_course"
            )
        ]

    def __str__(self):
        return f"{self.student}, {self.course}"


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

# helper function
def random_qr():
    """Randomly generate a 50-character qr_identifier for Lecture"""
    chars = string.ascii_letters + string.digits
    identifier = random.choices(chars, k=50)
    return ''.join(identifier)

class Lecture(models.Model):
    """Stores information about lectures"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    qr_identifier = models.CharField(max_length=50, unique=True, default=random_qr)
    date = models.DateField()

    def __str__(self):
        return f"{self.lecture_id}"


# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------

class QRCodeUpload(models.Model):
    """Stores information about student uploads"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, null=True, blank=True)
    photo = models.ImageField()
    uploaded_at = models.DateTimeField(auto_now_add=True)



# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------

# moved random_qr to before Lecture since it was giving me errors when I leave it
# down here.

def getUploadsForCourse(course):
    """
    course: the course number/name, e.g. "DATA13600" (stored in course_name).
    Returns QRCodeUpload objects for that course whose timestamp falls on a
    meeting day and between start_time and end_time (inclusive).
    """
    cl = Course.objects.filter(course_name=course).first()

    start = cl.start_time
    end = cl.end_time

    if isinstance(start, str):
        start = datetime.strptime(start.strip(), "%H:%M").time()
    if isinstance(end, str):
        end = datetime.strptime(end.strip(), "%H:%M").time()

    class_meeting_days = [
        cl.monday,
        cl.tuesday,
        cl.wednesday,
        cl.thursday,
        cl.friday,
    ]

    uploads = QRCodeUpload.objects.filter(lecture__course=cl).select_related("student__user", "lecture")

    good_uploads = []
    for upload in uploads:
        weekday = upload.uploaded_at.astimezone(CDT).weekday()
        if weekday in (5, 6) or not class_meeting_days[weekday]:
            continue
        upload_time = upload.uploaded_at.astimezone(CDT).time()
        if start <= upload_time <= end:
            good_uploads.append(upload)
    return good_uploads