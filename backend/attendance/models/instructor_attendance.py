from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from courses.models import Lecture, Weekday
from users.models import CustomUser, Instructor


class SupervisorSchedule(models.Model):
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name="attendance_supervisor_schedules",
        verbose_name=_("المعلم/المشرف"),
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=Weekday.choices, verbose_name=_("يوم الأسبوع")
    )
    start_time = models.TimeField(verbose_name=_("وقت البدء"))
    end_time = models.TimeField(verbose_name=_("وقت الانتهاء"))

    grace_period_minutes = models.PositiveIntegerField(
        default=20, verbose_name=_("دقائق فترة السماح")
    )
    auto_absent_after_minutes = models.PositiveIntegerField(
        default=60, verbose_name=_("دقائق الغياب التلقائي")
    )

    class Meta:
        unique_together = ("instructor", "day_of_week")
        verbose_name = "سجل حضور مدرس/مشرف"
        verbose_name_plural = "جداول حضور المدرسين/المشرفين"

    def clean(self):
        """Validate schedule constraints."""
        # Ensure that end_time is after start_time
        if self.start_time >= self.end_time:
            raise ValidationError({"end_time": _("End time must be after start time.")})

        # Check for overlapping schedules for the same instructor on the same day
        overlapping = SupervisorSchedule.objects.filter(
            instructor=self.instructor, day_of_week=self.day_of_week
        ).exclude(pk=self.pk)

        for existing in overlapping:
            # Check if times overlap
            if (
                self.start_time < existing.end_time
                and self.end_time > existing.start_time
            ):
                raise ValidationError(
                    _("This schedule overlaps with an existing schedule: %(schedule)s")
                    % {"schedule": str(existing)}
                )

    def __str__(self):
        return f"{self.instructor} — {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class AttendanceStatus(models.TextChoices):
    PENDING = "pending", _("منتظر")
    PRESENT = "present", _("حاضر")
    ABSENT = "absent", _("غائب")
    LATE = "late", _("متأخر")
    NOT_STARTED = "not_started", _("لم يبدأ")


class AttendanceType(models.TextChoices):
    """Type of attendance record - lecture-based or supervision schedule."""

    LECTURE = "lecture", _("محاضرة")
    SUPERVISION = "supervision", _("إشراف")


class CheckInMethod(models.TextChoices):
    """Method used for check-in/check-out."""

    FINGERPRINT = "fingerprint", _("بصمة الإصبع")
    RFID = "rfid", _("بطاقة RFID")
    MANUAL = "manual", _("يدوي بواسطة المشرف")
    QR_CODE = "qr_code", _("رمز QR")


class InstructorAttendance(models.Model):
    """Track attendance and rating of instructors (check-in/check-out)."""

    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("المعلم/المشرف"),
    )
    date = models.DateField(default=timezone.localdate, verbose_name=_("التاريخ"))
    check_in_time = models.DateTimeField(
        null=True, blank=True, verbose_name=_("وقت تسجيل الدخول")
    )
    check_out_time = models.DateTimeField(
        null=True, blank=True, verbose_name=_("وقت تسجيل الخروج")
    )

    check_in_method = models.CharField(
        max_length=20,
        choices=CheckInMethod.choices,
        null=True,
        blank=True,
        verbose_name=_("طريقة تسجيل الدخول"),
    )
    check_out_method = models.CharField(
        max_length=20,
        choices=CheckInMethod.choices,
        null=True,
        blank=True,
        verbose_name=_("طريقة تسجيل الخروج"),
    )

    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.NOT_STARTED,
        verbose_name=_("الحالة"),
    )

    attendance_type = models.CharField(
        max_length=20,
        choices=AttendanceType.choices,
        default=AttendanceType.LECTURE,
        verbose_name=_("نوع الحضور"),
    )

    schedule = models.ForeignKey(
        SupervisorSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendances",
        help_text=_("يوم جدول زمني مرتبط إذا كان هذا المدرب مشرفًا."),
    )
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instructor_attendances",
    )

    check_in_device = models.ForeignKey(
        "attendance.AttendanceDevice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="check_ins",
        verbose_name=_("جهاز تسجيل الدخول"),
    )
    check_out_device = models.ForeignKey(
        "attendance.AttendanceDevice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="check_outs",
        verbose_name=_("جهاز تسجيل الخروج"),
    )
    season = models.ForeignKey(
        "courses.Season",
        on_delete=models.CASCADE,
        related_name="instructor_attendance",
        verbose_name=_("الموسم"),
    )

    # Rating: null if absent/not_started, 0 if attended (default), then admin can update
    rating = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name=_("التقييم (1.00 - 10.00)"),
        validators=[MinValueValidator(0.00), MaxValueValidator(10.00)],
        null=True,
        blank=True,
        help_text=_("null للغائب، 0 للحاضر بدون تقييم، 1-10 للتقييم الفعلي"),
    )

    rated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="given_instructor_ratings",
        verbose_name=_("تم التقييم بواسطة"),
        help_text=_("المشرف/الأدمن الذي قام بتقييم هذا المعلم."),
    )

    rated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("وقت التقييم"),
        help_text=_("تاريخ ووقت إضافة/تحديث التقييم"),
    )

    notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات عامة"))

    class Meta:
        verbose_name = _("سجل حضور معلم/مشرف")
        verbose_name_plural = _("سجلات حضور المعلمين/المشرفين")
        # Allow multiple attendance records per day (lecture + supervision)
        # Each lecture or schedule can only have one attendance record per instructor per day
        constraints = [
            # For lecture attendance: one record per instructor per lecture
            models.UniqueConstraint(
                fields=["instructor", "lecture"],
                condition=models.Q(lecture__isnull=False),
                name="unique_instructor_lecture_attendance",
            ),
            # For supervision attendance: one record per instructor per schedule per date
            models.UniqueConstraint(
                fields=["instructor", "schedule", "date"],
                condition=models.Q(schedule__isnull=False),
                name="unique_instructor_schedule_date_attendance",
            ),
        ]
        indexes = [
            models.Index(fields=["instructor", "date"]),
            models.Index(fields=["season"]),
            models.Index(fields=["rated_by"]),
            models.Index(fields=["attendance_type"]),
            models.Index(fields=["status", "date"]),
        ]

    def __str__(self):
        rating_display = (
            f"{self.rating}/10" if self.rating is not None else "لم يتم التقييم"
        )
        return f"{self.instructor} - {rating_display} on {self.date}"

    def clean(self):
        """Validate attendance record constraints."""
        # Validate attendance_type consistency with lecture/schedule
        if self.attendance_type == AttendanceType.LECTURE:
            if self.schedule is not None:
                raise ValidationError(
                    {
                        "schedule": _(
                            "Lecture attendance should not have a schedule attached."
                        )
                    }
                )
        elif self.attendance_type == AttendanceType.SUPERVISION:
            if self.lecture is not None:
                raise ValidationError(
                    {
                        "lecture": _(
                            "Supervision attendance should not have a lecture attached."
                        )
                    }
                )

        # Validate check-out time is after check-in time
        if self.check_out_time and self.check_in_time:
            if self.check_out_time <= self.check_in_time:
                raise ValidationError(
                    {"check_out_time": _("Check-out time must be after check-in time.")}
                )

        # Cannot check out without checking in first
        if self.check_out_time and not self.check_in_time:
            raise ValidationError(
                {"check_out_time": _("Cannot check out without checking in first.")}
            )

        # Rating validations
        # If absent, not started, or pending, rating MUST be null
        if self.status in [
            AttendanceStatus.ABSENT,
            AttendanceStatus.NOT_STARTED,
            AttendanceStatus.PENDING,
        ]:
            if self.rating is not None:
                raise ValidationError(
                    {
                        "rating": _(
                            "لا يمكن تقييم المعلم الغائب أو الذي لم يبدأ. يجب أن يكون التقييم فارغاً."
                        )
                    }
                )

        # If present or late, rating can be None (not rated), 0 (attended but not rated), or 1-10
        elif self.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]:
            # If rating is provided and not 0, it must be between 1 and 10
            if self.rating is not None and self.rating > 0:
                if self.rating < 1 or self.rating > 10:
                    raise ValidationError(
                        {"rating": _("التقييم يجب أن يكون بين 1.00 و 10.00")}
                    )
                # If rating is provided (not 0), rated_by should also be provided
                if not self.rated_by:
                    raise ValidationError(
                        {"rated_by": _("يجب تحديد المقيّم عند إضافة التقييم.")}
                    )

    def save(self, *args, **kwargs):
        """Override save to automatically set rating based on attendance status."""
        # Ensure date is date only (no time component)
        if isinstance(self.date, timezone.datetime):
            self.date = self.date.date()

        # Auto-set rating based on status
        if self.status in [
            AttendanceStatus.ABSENT,
            AttendanceStatus.NOT_STARTED,
            AttendanceStatus.PENDING,
        ]:
            # If absent or not started, rating should be null
            if self.rating == 0:
                self.rating = None
        elif self.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]:
            # If present or late, and rating is null, set it to 0 (not rated yet)
            if self.rating is None:
                self.rating = 0.00

        super().save(*args, **kwargs)

    def broadcast_update(self):
        """Broadcast attendance update to connected WebSocket clients.

        Silently fails if Redis/channel layer is unavailable (e.g., during tests).
        """

        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
            async_to_sync(channel_layer.group_send)(
                "attendance_live",
                {
                    "type": "attendance_update",
                    "data": {
                        "id": self.id,
                        "instructor": self.instructor.user.get_full_name(),
                        "instructor_id": self.instructor.id,
                        "scheduled_check_in_time": (
                            str(self.lecture.start_time)
                            if self.attendance_type == AttendanceType.LECTURE
                            else str(self.schedule.start_time)
                        ),
                        "scheduled_check_out_time": (
                            str(self.lecture.end_time)
                            if self.attendance_type == AttendanceType.LECTURE
                            else str(self.schedule.end_time)
                        ),
                        "check_in_time": (
                            str(self.check_in_time) if self.check_in_time else None
                        ),
                        "check_out_time": (
                            str(self.check_out_time) if self.check_out_time else None
                        ),
                        "status": self.status,
                        "date": str(self.date),
                    },
                },
            )
        except Exception:
            # Silently fail if channel layer is not available (e.g., during tests)
            pass

    def mark_checked_in(self, device=None, method=CheckInMethod.FINGERPRINT):
        """Mark the instructor as checked in.

        Args:
            device: The attendance device used for check-in
            method: The method used for check-in (fingerprint, RFID, etc.)
        """
        now = timezone.now()
        self.check_in_time = now
        self.check_in_device = device
        self.check_in_method = method

        if self.schedule:
            shift_start = timezone.make_aware(
                timezone.datetime.combine(self.date, self.schedule.start_time)
            )
            if now > shift_start + timezone.timedelta(
                minutes=self.schedule.grace_period_minutes
            ):
                self.status = AttendanceStatus.LATE
            else:
                self.status = AttendanceStatus.PRESENT
        else:
            # If no schedule linked → treat as present by default
            self.status = AttendanceStatus.PRESENT

        # Set rating to 0 when instructor attends (not rated yet)
        self.rating = 0.00

        self.save()
        self.broadcast_update()

    def mark_checked_out(self, device=None, method=CheckInMethod.FINGERPRINT):
        """Mark the instructor as checked out.

        Args:
            device: The attendance device used for check-out
            method: The method used for check-out (fingerprint, RFID, etc.)

        Raises:
            ValidationError: If instructor hasn't checked in yet
        """
        if not self.check_in_time:
            raise ValidationError(_("Cannot check out without checking in first."))

        now = timezone.now()
        if now <= self.check_in_time:
            raise ValidationError(_("Check-out time must be after check-in time."))

        self.check_out_time = now
        self.check_out_device = device
        self.check_out_method = method
        self.save()
        self.broadcast_update()

    def mark_absent(self):
        """Mark the instructor as absent for the day."""
        self.status = AttendanceStatus.ABSENT
        # Set rating to null for absent instructors
        self.rating = None
        self.rated_by = None
        self.rated_at = None
        self.save()

    def add_rating(self, value: float, admin_user: CustomUser, notes: str = None):
        """
        Add or update rating for an instructor who attended.
        Can only rate instructors who are present or late.
        Admin can update rating multiple times (last one wins).

        Args:
            value: Rating value between 1.00 and 10.00
            admin_user: The admin user adding the rating
            notes: Optional notes/comments about the rating

        Raises:
            ValidationError: If trying to rate absent instructor or invalid rating
        """
        # Validate that instructor attended
        if self.status in [
            AttendanceStatus.ABSENT,
            AttendanceStatus.NOT_STARTED,
            AttendanceStatus.PENDING,
        ]:
            raise ValidationError(
                _("لا يمكن تقييم المعلم الذي لم يحضر. الحالة الحالية: {}").format(
                    self.get_status_display()
                )
            )

        # Validate rating range
        if value < 1.00 or value > 10.00:
            raise ValidationError(_("التقييم يجب أن يكون بين 1.00 و 10.00"))

        # Update rating fields
        self.rating = value
        self.rated_by = admin_user
        self.rated_at = timezone.now()
        self.notes = notes

        self.save()
        self.broadcast_rating()
        return self

    def broadcast_rating(self):
        """Broadcast rating update to connected WebSocket clients.

        Silently fails if Redis/channel layer is unavailable (e.g., during tests).
        """
        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
            async_to_sync(channel_layer.group_send)(
                "attendance_live",
                {
                    "type": "attendance_rated",
                    "data": {
                        "id": self.id,
                        "instructor": self.instructor.user.get_full_name(),
                        "instructor_id": str(self.instructor.user.id),
                        "rating": float(self.rating) if self.rating else None,
                        "rated_by": self.rated_by.get_full_name() if self.rated_by else None,
                        "rated_by_id": str(self.rated_by.id) if self.rated_by else None,
                        "rated_at": self.rated_at.isoformat() if self.rated_at else None,
                        "notes": self.notes,
                        "date": str(self.date),
                        "status": self.status,
                    },
                },
            )
        except Exception:
            # Silently fail if channel layer is not available (e.g., during tests)
            pass

    @classmethod
    def generate_for_date_range(cls, start_date, end_date, season=None):
        """
        Generate attendance records for:
        - Supervisors based on their weekly schedules (AttendanceType.SUPERVISION)
        - Instructors assigned to lectures within the date range (AttendanceType.LECTURE)

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            season: Optional Season instance. If not provided, uses the active season.

        Returns:
            int: Number of attendance records created
        """
        from datetime import timedelta
        from courses.models import Lecture, Season as SeasonModel, Weekday

        # Get the active season if not provided
        if season is None:
            season = SeasonModel.objects.filter(is_active=True).first()
            if season is None:
                # No active season found, cannot create attendance records
                return 0

        created_count = 0
        current_date = start_date

        while current_date <= end_date:

            # Supervisors: Generate based on weekly schedule
            # day_of_week uses the Weekday enum (Sat=0), not Python's Mon=0
            weekday = Weekday.of(current_date)
            for schedule in SupervisorSchedule.objects.filter(day_of_week=weekday):
                obj, created = cls.objects.get_or_create(
                    instructor=schedule.instructor,
                    schedule=schedule,
                    date=current_date,
                    defaults={
                        "attendance_type": AttendanceType.SUPERVISION,
                        "status": AttendanceStatus.NOT_STARTED,
                        "season": season,
                    },
                )
                if created:
                    created_count += 1

            # Normal instructors: Assign based on lectures that date
            for lecture in Lecture.objects.filter(day=current_date):
                if lecture.instructor is None:
                    continue  # Skip lectures without assigned instructor

                obj, created = cls.objects.get_or_create(
                    instructor=lecture.instructor,
                    lecture=lecture,
                    defaults={
                        "date": current_date,
                        "attendance_type": AttendanceType.LECTURE,
                        "status": AttendanceStatus.NOT_STARTED,
                        "season": season,
                    },
                )
                if created:
                    created_count += 1

            current_date += timedelta(days=1)

        return created_count

    @classmethod
    def generate_weekly(cls):
        today = timezone.localdate()
        start = today
        end = today + timezone.timedelta(days=7)
        return cls.generate_for_date_range(start, end)
