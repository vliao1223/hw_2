"""
LLM: Claude Sonnet 5.5

Prompt:

AttendanceChimp tracks class attendance via QR codes:
• Users: students and instructors (two roles).
• Courses: each has one instructor. Students can enroll in multiple courses.
• Lectures: individual class meetings, each associated with a course.
• QR Code Uploads: photos uploaded by students, each associated with a student and a
Lecture.

Required Tables:
• InstructorProfile / StudentProfile tables (instead of one Users table)
• Course table with at least name, instructor, meeting schedule
• Enrollment table: links students to courses (many-to-many)
• Lecture table: linked to a course, has a date and a QR identifier
• QRCodeUpload table: linked to a student and (optionally) a lecture

Generate the models.py file.
"""

''' Below are the AI ouputs '''
# ------------------------------------------------------------------------------



"""
AttendanceChimp data models.

Roles are modeled as separate profile tables (InstructorProfile / StudentProfile),
each attached one-to-one to Django's auth user, instead of a single Users table.
"""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #
class InstructorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
    )
    department = models.CharField(max_length=100, blank=True)
    office = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    student_id = models.CharField(
        max_length=32,
        unique=True,
        help_text="University-issued student ID number.",
    )
    major = models.CharField(max_length=100, blank=True)

    # Many-to-many to Course, realized through the Enrollment table below.
    courses = models.ManyToManyField(
        "Course",
        through="Enrollment",
        related_name="students",
        blank=True,
    )

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        name = self.user.get_full_name() or self.user.get_username()
        return f"{name} ({self.student_id})"


# --------------------------------------------------------------------------- #
# Courses & enrollment
# --------------------------------------------------------------------------- #
class Course(models.Model):
    # Meeting days stored as a compact string of letters, e.g. "MWF" or "TR".
    # M=Mon, T=Tue, W=Wed, R=Thu, F=Fri, S=Sat, U=Sun
    DAYS_VALIDATOR = RegexValidator(
        regex=r"^(?!.*(.).*\1)[MTWRFSU]+$",
        message="Use unique day letters from M, T, W, R, F, S, U (e.g. 'MWF', 'TR').",
    )

    name = models.CharField(max_length=200)
    code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Optional catalog code, e.g. CS101.",
    )
    term = models.CharField(
        max_length=30,
        blank=True,
        help_text="e.g. 'Fall 2026'.",
    )

    # Each course has exactly one instructor. PROTECT prevents silently deleting
    # a course (and its attendance history) when an instructor is removed.
    instructor = models.ForeignKey(
        InstructorProfile,
        on_delete=models.PROTECT,
        related_name="courses",
    )

    # Meeting schedule
    meeting_days = models.CharField(
        max_length=7,
        validators=[DAYS_VALIDATOR],
        help_text="Letters for days the class meets: M T W R F S U (e.g. 'MWF').",
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="course_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.code + ' - ' if self.code else ''}{self.name}"


class Enrollment(models.Model):
    """Join table: a student enrolled in a course (many-to-many)."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course", "student"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course_enrollment",
            ),
        ]

    def __str__(self):
        return f"{self.student} -> {self.course}"


# --------------------------------------------------------------------------- #
# Lectures & QR uploads
# --------------------------------------------------------------------------- #
def generate_qr_identifier():
    return uuid.uuid4().hex


class Lecture(models.Model):
    """A single class meeting of a course."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lectures",
    )
    date = models.DateField()
    title = models.CharField(max_length=200, blank=True)

    # Value encoded in the QR code displayed during this lecture.
    qr_identifier = models.CharField(
        max_length=64,
        unique=True,
        default=generate_qr_identifier,
        editable=False,
        help_text="Unique token encoded in this lecture's QR code.",
    )

    class Meta:
        ordering = ["-date"]
        constraints = [
            # One lecture per course per date. Remove if a course can meet
            # more than once a day.
            models.UniqueConstraint(
                fields=["course", "date"],
                name="unique_lecture_per_course_per_day",
            ),
        ]

    def __str__(self):
        return f"{self.course} - {self.date}"


def qr_upload_path(instance, filename):
    return f"qr_uploads/student_{instance.student_id}/{uuid.uuid4().hex}_{filename}"


class QRCodeUpload(models.Model):
    """A photo of a QR code uploaded by a student as proof of attendance."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="qr_uploads",
    )
    # Optional: an upload may arrive before the QR code is decoded/matched.
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="qr_uploads",
    )
    image = models.ImageField(upload_to=qr_upload_path)  # requires Pillow
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def clean(self):
        # A student may only be linked to lectures of courses they're enrolled in.
        if self.lecture_id and self.student_id:
            enrolled = Enrollment.objects.filter(
                student_id=self.student_id,
                course_id=self.lecture.course_id,
            ).exists()
            if not enrolled:
                raise ValidationError(
                    "Student is not enrolled in the course for this lecture."
                )

    def __str__(self):
        target = self.lecture if self.lecture_id else "unmatched"
        return f"Upload by {self.student} ({target})"