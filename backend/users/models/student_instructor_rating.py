from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator


class StudentInstructorRating(models.Model):
    """Model representing ratings given by students to instructors."""

    student = models.ForeignKey(
        "users.StudentUser", on_delete=models.CASCADE, related_name="instructor_ratings"
    )
    instructor = models.ForeignKey(
        "users.Instructor",
        on_delete=models.CASCADE,
        related_name="student_ratings",
        verbose_name="المعلم",
    )
    # The course the rater took with this instructor: exactly one of a
    # physical course or an online course.
    course = models.ForeignKey(
        "courses.Course",
        verbose_name="الدورة",
        on_delete=models.CASCADE,
        related_name="student_instructor_ratings",
        null=True,
        blank=True,
    )
    online_course = models.ForeignKey(
        "courses_online.OnlineCourse",
        verbose_name="الدورة الإلكترونية",
        on_delete=models.CASCADE,
        related_name="student_instructor_ratings",
        null=True,
        blank=True,
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name="التقييم",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for StudentInstructorRating model."""

        constraints = [
            # Ensure rating is between 1.00 and 10.00
            models.CheckConstraint(
                condition=Q(rating__gte=1.00, rating__lte=10.00),
                name="student_instructor_rating_range",
            ),
            models.CheckConstraint(
                condition=(
                    Q(course__isnull=False, online_course__isnull=True)
                    | Q(course__isnull=True, online_course__isnull=False)
                ),
                name="student_instructor_rating_one_course",
            ),
            models.UniqueConstraint(
                fields=["student", "instructor"],
                name="unique_student_instructor_rating",
            ),
        ]
        indexes = [models.Index(fields=["student"], name="rating_student_index")]

        verbose_name = "تقييم طالب لمدرس"
        verbose_name_plural = "تقييمات الطلاب للمدرسين"

    def __str__(self):
        return 'تقييم الطالب "{}" للمدرس "{}"'.format(
            self.student.user.get_full_name(), self.instructor.user.get_full_name()
        )


class ParentInstructorRating(models.Model):
    """Model representing ratings given by parents to instructors."""

    parent = models.ForeignKey(
        "parents.Parent", on_delete=models.CASCADE, related_name="instructor_ratings"
    )
    instructor = models.ForeignKey(
        "users.Instructor",
        on_delete=models.CASCADE,
        related_name="parent_ratings",
        verbose_name="المعلم",
    )
    # The course the rater took with this instructor: exactly one of a
    # physical course or an online course.
    course = models.ForeignKey(
        "courses.Course",
        verbose_name="الدورة",
        on_delete=models.CASCADE,
        related_name="parent_instructor_ratings",
        null=True,
        blank=True,
    )
    online_course = models.ForeignKey(
        "courses_online.OnlineCourse",
        verbose_name="الدورة الإلكترونية",
        on_delete=models.CASCADE,
        related_name="parent_instructor_ratings",
        null=True,
        blank=True,
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name="التقييم",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for ParentInstructorRating model."""

        constraints = [
            # Ensure rating is between 1.00 and 10.00
            models.CheckConstraint(
                condition=Q(rating__gte=1.00, rating__lte=10.00),
                name="parent_instructor_rating_range",
            ),
            models.CheckConstraint(
                condition=(
                    Q(course__isnull=False, online_course__isnull=True)
                    | Q(course__isnull=True, online_course__isnull=False)
                ),
                name="parent_instructor_rating_one_course",
            ),
            models.UniqueConstraint(
                fields=["parent", "instructor"], name="unique_parent_instructor_rating"
            ),
        ]
        indexes = [models.Index(fields=["parent"], name="rating_parent_index")]

        verbose_name = "تقييم ولي أمر لمدرس"
        verbose_name_plural = "تقييمات أولياء الأمور للمدرسين"

    def __str__(self):
        return 'تقييم ولي الأمر "{}" للمدرس "{}"'.format(
            self.parent.user.get_full_name(), self.instructor.user.get_full_name()
        )


class StudentCourseRating(models.Model):
    """Model representing ratings given by students to courses."""

    student = models.ForeignKey(
        "users.StudentUser", on_delete=models.CASCADE, related_name="course_ratings"
    )
    course = models.ForeignKey(
        "courses.Course",
        verbose_name="الدورة",
        on_delete=models.CASCADE,
        related_name="student_ratings",
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name="التقييم",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for StudentCourseRating model."""

        constraints = [
            # Ensure rating is between 1.00 and 10.00
            models.CheckConstraint(
                condition=Q(rating__gte=1.00, rating__lte=10.00),
                name="student_course_rating_range",
            ),
            models.UniqueConstraint(
                fields=["student", "course"], name="unique_student_course_rating"
            ),
        ]
        indexes = [
            models.Index(fields=["student"], name="course_rating_student_index"),
            models.Index(fields=["course"], name="student_course_rating_index"),
        ]

        verbose_name = "تقييم طالب لكورس"
        verbose_name_plural = "تقييمات الطلاب للكورسات"

    def __str__(self):
        return 'تقييم الطالب "{}" للكورس "{}"'.format(
            self.student.user.get_full_name(), self.course.name
        )


class ParentCourseRating(models.Model):
    """Model representing ratings given by parents to courses."""

    parent = models.ForeignKey(
        "parents.Parent", on_delete=models.CASCADE, related_name="course_ratings"
    )
    course = models.ForeignKey(
        "courses.Course",
        verbose_name="الدورة",
        on_delete=models.CASCADE,
        related_name="parent_ratings",
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name="التقييم",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for ParentCourseRating model."""

        constraints = [
            # Ensure rating is between 1.00 and 10.00
            models.CheckConstraint(
                condition=Q(rating__gte=1.00, rating__lte=10.00),
                name="parent_course_rating_range",
            ),
            models.UniqueConstraint(
                fields=["parent", "course"], name="unique_parent_course_rating"
            ),
        ]
        indexes = [
            models.Index(fields=["parent"], name="course_rating_parent_index"),
            models.Index(fields=["course"], name="parent_course_rating_index"),
        ]

        verbose_name = "تقييم ولي أمر لكورس"
        verbose_name_plural = "تقييمات أولياء الأمور للكورسات"

    def __str__(self):
        return 'تقييم ولي الأمر "{}" للكورس "{}"'.format(
            self.parent.user.get_full_name(), self.course.name
        )


class StudentOnlineCourseRating(models.Model):
    """Model representing ratings given by students to online courses."""

    student = models.ForeignKey('users.StudentUser', on_delete=models.CASCADE,
                                related_name='online_course_ratings')
    course = models.ForeignKey('courses_online.OnlineCourse', verbose_name="الدورة", on_delete=models.CASCADE,
                               related_name='student_ratings')
    rating = models.PositiveSmallIntegerField(
        verbose_name="التقييم",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for StudentOnlineCourseRating model."""
        constraints = [
            # Ensure rating is between 1.00 and 10.00
            models.CheckConstraint(
                condition=Q(rating__gte=1.00, rating__lte=10.00),
                name='student_online_course_rating_range'
            ),
            models.UniqueConstraint(
                fields=['student', 'course'],
                name='unique_student_online_course_rating'
            )
        ]
        indexes = [
            models.Index(fields=['student'],
                         name='online_rating_student_index'),
            models.Index(fields=['course'], name='student_online_rating_index')
        ]

        verbose_name = 'تقييم طالب لكورس أونلاين'
        verbose_name_plural = 'تقييمات الطلاب للكورسات الأونلاين'

    def __str__(self):
        return 'تقييم الطالب "{}" للكورس "{}"'.format(
            self.student.user.get_full_name(), self.course.name
        )


class ParentOnlineCourseRating(models.Model):
    """Model representing ratings given by parents to online courses."""

    parent = models.ForeignKey('parents.Parent', on_delete=models.CASCADE,
                               related_name='online_course_ratings')
    course = models.ForeignKey('courses_online.OnlineCourse', verbose_name="الدورة", on_delete=models.CASCADE,
                               related_name='parent_ratings')
    rating = models.PositiveSmallIntegerField(
        verbose_name="التقييم",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for ParentOnlineCourseRating model."""
        constraints = [
            # Ensure rating is between 1.00 and 10.00
            models.CheckConstraint(
                condition=Q(rating__gte=1.00, rating__lte=10.00),
                name='parent_online_course_rating_range'
            ),
            models.UniqueConstraint(
                fields=['parent', 'course'],
                name='unique_parent_online_course_rating'
            )
        ]
        indexes = [
            models.Index(fields=['parent'], name='online_rating_parent_index'),
            models.Index(fields=['course'], name='parent_online_rating_index')
        ]

        verbose_name = 'تقييم ولي أمر لكورس أونلاين'
        verbose_name_plural = 'تقييمات أولياء الأمور للكورسات الأونلاين'

    def __str__(self):
        return 'تقييم ولي الأمر "{}" للكورس "{}"'.format(
            self.parent.user.get_full_name(), self.course.name
        )
