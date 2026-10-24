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

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------
class studentProfile(models.Model):
    """Stores profile information for students."""
    student_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    school_email = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.student_id}"

class instructorProfile(models.Model):
    """Stores profile information for instructors."""
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

class course(models.Model):
    """Stores information about courses."""
    course_id = models.CharField(primary_key=True, max_length=50)
    course_name = models.CharField(max_length=50, unique=True)
    instructor = models.ForeignKey(instructorProfile, on_delete=models.SET_NULL, null=True)
    meeting_days = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course_id}"


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class enrollment(models.Model):
    """Junction table for Student and Course"""
    student = models.ForeignKey(studentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(course, on_delete=models.CASCADE)
    pk = models.CompositePrimaryKey("student_id", "course_id")

    def __str__(self):
        return f"{self.student}, {self.course}"


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

class lecture(models.Model):
    """Stores information about lectures"""
    lecture_id = models.CharField(primary_key=True, max_length=50)
    course = models.ForeignKey(course, on_delete=models.CASCADE)
    qr_identifier = models.CharField(max_length=50, unique=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.lecture_id}"


# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------

class qrCodeUpload(models.Model):
    """Stores information about student uploads"""
    qr_id = models.CharField(primary_key=True, max_length=50)
    student = models.ForeignKey(studentProfile, on_delete=models.CASCADE)
    lecture = models.ForeignKey(lecture, on_delete=models.CASCADE)
    photo = models.ImageField()
    uploaded_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.lecture_id}"


# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------



