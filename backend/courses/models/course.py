#!/usr/bin/env python3
''' Models for Course app'''
from datetime import timedelta
from cloudinary.models import CloudinaryField
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Count, Q

# Create your models here.


# ---------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------

class SeasonChoices(models.TextChoices):
    """Enumeration for season_type status choices."""
    SUMMER_CAMP = 'summer_camp', _('معسكر صيفي')
    SCHOOL = 'school',      _('مدرسة')
    RAMADAN = 'ramadan',     _('رمضان')
    EID = 'eid',         _('عيد')
    MID_YEAR = 'mid_year',    _('معسكر منتصف السنة')
    OTHER = 'other',       _('أخرى')


class Weekday(models.IntegerChoices):
    """Enumeration for weekday choices."""
    SATURDAY = 0, _('Saturday')
    SUNDAY = 1, _('Sunday')
    MONDAY = 2, _('Monday')
    TUESDAY = 3, _('Tuesday')
    WEDNESDAY = 4, _('Wednesday')
    THURSDAY = 5, _('Thursday')
    FRIDAY = 6, _('Friday')

    @classmethod
    def of(cls, day) -> int:
        """Weekday value (Sat=0..Fri=6) of a date; Python's weekday() is Mon=0..Sun=6."""
        return (day.weekday() + 2) % 7


class Season(models.Model):
    """
    Season model
    """

    # consider adding a celery task to deactivate old seasons and activate new ones based on dates
    name = models.CharField(max_length=128, verbose_name=_("اسم الموسم"))
    season_type = models.CharField(
        max_length=32, choices=SeasonChoices.choices, verbose_name=_("نوع الموسم"))
    start_date = models.DateField(verbose_name=_("تاريخ البدء"))
    end_date = models.DateField(
        null=True, blank=True, verbose_name=_("تاريخ الانتهاء"))
    description = models.TextField(
        blank=True, null=True, verbose_name=_("الوصف"))
    is_active = models.BooleanField(default=False, verbose_name=_("نشط"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True)

    # we could cache number of lectures and enrolled students

    class Meta:
        indexes = [
            models.Index(fields=['start_date'], name='season_start_date_idx'),
            models.Index(fields=['end_date'],   name='season_end_date_idx'),
        ]
        ordering = ['-start_date', 'name']
        verbose_name = _("موسم")
        verbose_name_plural = _("المواسم")

    def clean(self):
        # end_date is optional. If provided, it must be >= start_date.
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                _("End date must be on or after start date."))

    def __str__(self):
        end = self.end_date or 'open'
        return f"{self.name} ({self.start_date} → {end})"
# Model Tag


class Tag(models.Model):
    """
    Tags model
    """

    name = models.CharField(max_length=50, unique=True,
                            verbose_name=_("اسم الفئة"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))

    class Meta:
        ordering = ['name']
        verbose_name = _("فئة كورس/مدرس")
        verbose_name_plural = _("فئات الكورسات/المدرسين")

    def __str__(self):
        return self.name

# Model Course


class Course(models.Model):
    """
    Course model
    """

    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    # Cloudinary image with automatic optimization:
    # - folder: organizes images in 'courses/' folder
    # - transformation: resizes to max 800px width, auto quality, auto format (webp/avif)
    image = CloudinaryField(
        'صورة الكورس',
        blank=True,
        null=True,
        folder='courses',
        transformation={
            'width': 800,
            'crop': 'limit',  # Only downscale, never upscale
            'quality': 'auto:good',  # Automatic quality optimization
            # Auto-select best format (webp, avif, etc.)
            'fetch_format': 'auto',
        },
    )
    start_date = models.DateField(verbose_name=_("تاريخ البدء"))
    # optional if you later drive off schedules/lectures
    end_date = models.DateField(null=True, blank=True)

    # compute this from Lectures or use it to compute lectures
    num_lectures = models.IntegerField(null=True, blank=True)
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True)

    season = models.ForeignKey('courses.Season', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="courses", verbose_name=_("الموسم"))
    instructor = models.ForeignKey('users.Instructor', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="courses", verbose_name=_("المعلم"))
    tags = models.ManyToManyField(
        'courses.Tag', related_name="courses", blank=True, verbose_name=_("الفئات"))
    for_adults = models.BooleanField(default=True, verbose_name=_("للبالغين"))
    min_age = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("الحد الأدنى للعمر"))
    max_age = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("الحد الأقصى للعمر"))

    slug = models.SlugField(max_length=150, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['instructor'], name='course_instructor_idx'),
            models.Index(fields=['season'],     name='course_season_idx'),
            models.Index(fields=['start_date'], name='course_start_date_idx'),
        ]
        ordering = ['-start_date', 'name']
        verbose_name = _("كورس")
        verbose_name_plural = _("الكورسات")

    def clean(self):
        '''Validate the course before saving'''
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                _("End date must be on or after start date."))

        # Require either end_date or num_lectures
        if not self.end_date and not self.num_lectures:
            raise ValidationError(
                _("Either 'end_date' or 'num_lectures' must be provided."))

        # 1 only of them
        # If bound to a season, the course window should be inside season (if season has an end)
        if self.season:
            if self.start_date < self.season.start_date:
                raise ValidationError(
                    _("Course start date cannot be before its season start date."))
            if self.season.end_date and self.end_date and self.end_date > self.season.end_date:
                raise ValidationError(
                    _("Course end date cannot be after its season end date."))

    @staticmethod
    def _system_weekday_to_python(system_weekday: int) -> int:
        """
        Convert Weekday enum (Sat=0..Fri=6) to Python's weekday() format
        where Monday=0..Sunday=6.
        """
        return (system_weekday + 5) % 7

    def is_participant_eligible(self, participant) -> bool:
        """Check if a participant (StudentUser or Child) is eligible for this course.

        Args:
            participant: Either a StudentUser or Child instance

        Returns:
            bool: True if participant is eligible, False otherwise
        """
        if not participant:
            return False

        # Check if participant is a Child (has no .user attribute)
        # or a StudentUser (has .user attribute)
        from parents.models import Child

        if isinstance(participant, Child):
            # Child has get_age_on_date directly
            age = participant.get_age_on_date(self.start_date)
            if age is None:
                return False
            # Children are typically not adults
            if self.for_adults:
                return False
            # Check age bounds if specified
            if self.min_age and age < self.min_age:
                return False
            if self.max_age and age > self.max_age:
                return False
            return True
        else:
            # StudentUser - has .user attribute
            if not hasattr(participant, 'user') or not participant.user:
                return False
            age = participant.user.get_age_on_date(self.start_date)
            if age is None:
                return False
            # Check for_adults constraint
            if self.for_adults and age < 15:
                return False
            # Check age bounds if specified
            if self.min_age and age < self.min_age:
                return False
            if self.max_age and age > self.max_age:
                return False
            if participant.user.role != "student":
                return False
            return True

    def generate_lectures(self):
        ''' Generate lectures based on course schedules
        Only used if all the Course Schedules for a course are created before any lectures.
        '''
        from .lecture import Lecture

        # Guard: skip if lectures already exist for this course
        if self.lectures.exists():
            return

        course_start_date = self.start_date
        course_end_date = self.end_date if self.end_date else None
        course_number_of_lectures = self.num_lectures if self.num_lectures else None

        schedules = list(self.schedules.all())
        if not schedules:
            return

        # Use a single timestamp for all lectures created in this batch
        now = timezone.now()
        lectures_to_create = []

        if course_end_date and not course_number_of_lectures:
            count = 0
            current_date = course_start_date
            while current_date <= course_end_date:
                for schedule in schedules:
                    python_weekday = self._system_weekday_to_python(
                        schedule.weekday)
                    if current_date.weekday() == python_weekday:
                        lectures_to_create.append(Lecture(
                            course=self,
                            day=current_date,
                            start_time=schedule.start_time,
                            end_time=schedule.end_time,
                            lecture_number=count + 1,
                            instructor=self.instructor,
                        ))
                        count += 1
                current_date += timedelta(days=1)
            self.num_lectures = count
        elif course_number_of_lectures:
            count = 0
            current_date = course_start_date
            end_date = None
            while count < course_number_of_lectures:
                for schedule in schedules:
                    python_weekday = self._system_weekday_to_python(
                        schedule.weekday)
                    if current_date.weekday() == python_weekday and count < course_number_of_lectures:
                        lectures_to_create.append(Lecture(
                            course=self,
                            day=current_date,
                            start_time=schedule.start_time,
                            end_time=schedule.end_time,
                            lecture_number=count + 1,
                            instructor=self.instructor,
                        ))
                        end_date = current_date
                        count += 1
                current_date += timedelta(days=1)
            self.end_date = end_date

        # Bulk create lectures for better performance
        if lectures_to_create:
            Lecture.objects.bulk_create(lectures_to_create, ignore_conflicts=True)
            # Update timestamps to be identical for all lectures in this batch
            lecture_ids = [lec.pk for lec in lectures_to_create]
            Lecture.objects.filter(pk__in=lecture_ids).update(
                created_at=now, updated_at=now)

        # Save the updated course fields (num_lectures or end_date)
        self.save(update_fields=['num_lectures', 'end_date', 'updated_at'])

    def save(self, *args, **kwargs):
        '''Override save to auto-generate slug if not provided.'''
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
            # Ensure slug uniqueness
            original_slug = self.slug
            counter = 1
            while Course.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    @property
    def enrolled_count(self):
        """Return count of active enrollments for this course."""
        return self.enrollments.filter(status='active').count()

    @property
    def available_spots(self):
        """Return number of available spots in the course."""
        return max(0, self.capacity - self.enrolled_count)

    @property
    def is_full(self):
        """Check if the course has reached capacity."""
        return self.enrolled_count >= self.capacity

    @property
    def average_rating(self):
        """Calculate and return the average rating for the course.

        Uses database aggregation for optimal performance instead of
        loading all ratings into memory.
        """
        # Use annotated value if available (from queryset optimization)
        if hasattr(self, '_average_rating'):
            return self._average_rating

        from django.db.models import Sum, Count
        from users.models.student_instructor_rating import StudentCourseRating, ParentCourseRating

        # Use database aggregation instead of loading all ratings into memory
        student_stats = StudentCourseRating.objects.filter(course=self).aggregate(
            total=Sum('rating'), count=Count('id')
        )
        parent_stats = ParentCourseRating.objects.filter(course=self).aggregate(
            total=Sum('rating'), count=Count('id')
        )

        total_sum = (student_stats['total'] or 0) + \
            (parent_stats['total'] or 0)
        total_count = (student_stats['count'] or 0) + \
            (parent_stats['count'] or 0)

        if total_count == 0:
            return None
        return total_sum / total_count

    @property
    def rating_count(self):
        """Return total number of ratings for this course."""
        if hasattr(self, '_rating_count'):
            return self._rating_count

        from users.models.student_instructor_rating import StudentCourseRating, ParentCourseRating

        student_count = StudentCourseRating.objects.filter(course=self).count()
        parent_count = ParentCourseRating.objects.filter(course=self).count()
        return student_count + parent_count


class CourseSchedule(models.Model):
    """
    Course Schedule mode
    """

    course = models.ForeignKey(
        'courses.Course', verbose_name="الدورة", on_delete=models.CASCADE, related_name='schedules')
    weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices, verbose_name=_("يوم الأسبوع"))
    start_time = models.TimeField()
    end_time = models.TimeField()

    def clean(self):
        '''Validate the course schedule.'''
        if self.end_time <= self.start_time:
            raise ValidationError(_("End time must be after start time."))

    class Meta:
        indexes = [
            models.Index(fields=['course'], name='course_schedule_course_idx'),
        ]
        ordering = ['course', 'weekday', 'start_time']
        verbose_name = _("ميعاد كورس")
        verbose_name_plural = _("مواعيد الكورسات")

    def __str__(self):
        return f"{self.course} — {self.get_weekday_display()} {self.start_time}-{self.end_time}"
