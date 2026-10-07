from django.contrib import admin
from core.utils import ExcelExportMixin
from users.models.student_instructor_rating import (
    StudentInstructorRating,
    ParentInstructorRating,
    StudentCourseRating,
    ParentCourseRating
)


@admin.register(StudentInstructorRating)
class StudentInstructorRatingAdmin(ExcelExportMixin, admin.ModelAdmin):
    list_display = ('action_checkbox', 'get_student', 'get_instructor',
                    'get_course', 'get_rating', 'get_created_at')
    list_filter = ('rating', 'course', 'instructor', 'created_at')
    search_fields = ('student__user__first_name',
                     'instructor__user__first_name', 'feedback')
    autocomplete_fields = ['student', 'instructor', 'course']
    date_hierarchy = 'created_at'
    list_select_related = ('student', 'student__user',
                           'instructor', 'instructor__user', 'course',
                           'online_course')

    fieldsets = (
        ('معلومات التقييم', {'fields': ('student', 'instructor', 'course', 'online_course')}),
        ('التقييم', {'fields': ('rating', 'feedback')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('student', 'instructor', 'course', 'online_course', 'rating', 'feedback'),
        }),
    )

    def get_student(self, obj):
        return obj.student
    get_student.short_description = 'الطالب'
    get_student.admin_order_field = 'student'

    def get_instructor(self, obj):
        return obj.instructor
    get_instructor.short_description = 'المدرس'
    get_instructor.admin_order_field = 'instructor'

    def get_course(self, obj):
        return obj.course or obj.online_course
    get_course.short_description = 'الدورة'
    get_course.admin_order_field = 'course'

    def get_rating(self, obj):
        return obj.rating
    get_rating.short_description = 'التقييم'
    get_rating.admin_order_field = 'rating'

    def get_created_at(self, obj):
        return obj.created_at
    get_created_at.short_description = 'تاريخ الإنشاء'
    get_created_at.admin_order_field = 'created_at'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'student' in form.base_fields:
            form.base_fields['student'].label = 'الطالب'
        if 'instructor' in form.base_fields:
            form.base_fields['instructor'].label = 'المدرس'
        if 'course' in form.base_fields:
            form.base_fields['course'].label = 'الدورة'
        if 'online_course' in form.base_fields:
            form.base_fields['online_course'].label = 'الدورة الإلكترونية'
        if 'rating' in form.base_fields:
            form.base_fields['rating'].label = 'التقييم'
        if 'feedback' in form.base_fields:
            form.base_fields['feedback'].label = 'الملاحظات'
        return form

    class Meta:
        verbose_name = 'تقييم طالب لمدرس'
        verbose_name_plural = 'تقييمات الطلاب للمدرسين'

    # Excel export configuration
    excel_filename = 'student_instructor_ratings'


@admin.register(ParentInstructorRating)
class ParentInstructorRatingAdmin(ExcelExportMixin, admin.ModelAdmin):
    list_display = ('action_checkbox', 'get_parent', 'get_instructor',
                    'get_course', 'get_rating', 'get_created_at')
    list_filter = ('rating', 'course', 'instructor', 'created_at')
    search_fields = ('parent__user__first_name',
                     'instructor__user__first_name', 'feedback')
    date_hierarchy = 'created_at'
    list_select_related = ('parent', 'parent__user',
                           'instructor', 'instructor__user', 'course',
                           'online_course')
    autocomplete_fields = ['parent', 'instructor', 'course']

    fieldsets = (
        ('معلومات التقييم', {'fields': ('parent', 'instructor', 'course', 'online_course')}),
        ('التقييم', {'fields': ('rating', 'feedback')}),
    )

    def get_parent(self, obj):
        return obj.parent
    get_parent.short_description = 'ولي الأمر'
    get_parent.admin_order_field = 'parent'

    def get_instructor(self, obj):
        return obj.instructor
    get_instructor.short_description = 'المدرس'
    get_instructor.admin_order_field = 'instructor'

    def get_course(self, obj):
        return obj.course or obj.online_course
    get_course.short_description = 'الدورة'
    get_course.admin_order_field = 'course'

    def get_rating(self, obj):
        return obj.rating
    get_rating.short_description = 'التقييم'
    get_rating.admin_order_field = 'rating'

    def get_created_at(self, obj):
        return obj.created_at
    get_created_at.short_description = 'تاريخ الإنشاء'
    get_created_at.admin_order_field = 'created_at'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'parent' in form.base_fields:
            form.base_fields['parent'].label = 'ولي الأمر'
        if 'instructor' in form.base_fields:
            form.base_fields['instructor'].label = 'المدرس'
        if 'course' in form.base_fields:
            form.base_fields['course'].label = 'الدورة'
        if 'online_course' in form.base_fields:
            form.base_fields['online_course'].label = 'الدورة الإلكترونية'
        if 'rating' in form.base_fields:
            form.base_fields['rating'].label = 'التقييم'
        if 'feedback' in form.base_fields:
            form.base_fields['feedback'].label = 'الملاحظات'
        return form

    class Meta:
        verbose_name = 'تقييم ولي أمر لمدرس'
        verbose_name_plural = 'تقييمات أولياء الأمور للمدرسين'

    # Excel export configuration
    excel_filename = 'parent_instructor_ratings'


@admin.register(StudentCourseRating)
class StudentCourseRatingAdmin(ExcelExportMixin, admin.ModelAdmin):
    list_display = ('action_checkbox', 'get_student', 'get_course',
                    'get_rating', 'get_created_at')
    list_filter = ('rating', 'course', 'created_at')
    search_fields = ('student__user__first_name', 'course__name', 'feedback')
    date_hierarchy = 'created_at'
    list_select_related = ('student', 'student__user', 'course')
    autocomplete_fields = ['student', 'course']
    fieldsets = (
        ('معلومات التقييم', {'fields': ('student', 'course')}),
        ('التقييم', {'fields': ('rating', 'feedback')}),
    )

    def get_student(self, obj):
        return obj.student
    get_student.short_description = 'الطالب'
    get_student.admin_order_field = 'student'

    def get_course(self, obj):
        return obj.course
    get_course.short_description = 'الدورة'
    get_course.admin_order_field = 'course'

    def get_rating(self, obj):
        return obj.rating
    get_rating.short_description = 'التقييم'
    get_rating.admin_order_field = 'rating'

    def get_created_at(self, obj):
        return obj.created_at
    get_created_at.short_description = 'تاريخ الإنشاء'
    get_created_at.admin_order_field = 'created_at'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'student' in form.base_fields:
            form.base_fields['student'].label = 'الطالب'
        if 'course' in form.base_fields:
            form.base_fields['course'].label = 'الدورة'
        if 'rating' in form.base_fields:
            form.base_fields['rating'].label = 'التقييم'
        if 'feedback' in form.base_fields:
            form.base_fields['feedback'].label = 'الملاحظات'
        return form

    class Meta:
        verbose_name = 'تقييم طالب لكورس'
        verbose_name_plural = 'تقييمات الطلاب للكورسات'

    # Excel export configuration
    excel_filename = 'student_course_ratings'


@admin.register(ParentCourseRating)
class ParentCourseRatingAdmin(ExcelExportMixin, admin.ModelAdmin):
    list_display = ('action_checkbox', 'get_parent', 'get_course', 'get_rating', 'get_created_at')
    list_filter = ('rating', 'course', 'created_at')
    search_fields = ('parent__user__first_name', 'course__name', 'feedback')
    date_hierarchy = 'created_at'
    list_select_related = ('parent', 'parent__user', 'course')
    autocomplete_fields = ['parent', 'course']
    fieldsets = (
        ('معلومات التقييم', {'fields': ('parent', 'course')}),
        ('التقييم', {'fields': ('rating', 'feedback')}),
    )

    def get_parent(self, obj):
        return obj.parent
    get_parent.short_description = 'ولي الأمر'
    get_parent.admin_order_field = 'parent'

    def get_course(self, obj):
        return obj.course
    get_course.short_description = 'الدورة'
    get_course.admin_order_field = 'course'

    def get_rating(self, obj):
        return obj.rating
    get_rating.short_description = 'التقييم'
    get_rating.admin_order_field = 'rating'

    def get_created_at(self, obj):
        return obj.created_at
    get_created_at.short_description = 'تاريخ الإنشاء'
    get_created_at.admin_order_field = 'created_at'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'parent' in form.base_fields:
            form.base_fields['parent'].label = 'ولي الأمر'
        if 'course' in form.base_fields:
            form.base_fields['course'].label = 'الدورة'
        if 'rating' in form.base_fields:
            form.base_fields['rating'].label = 'التقييم'
        if 'feedback' in form.base_fields:
            form.base_fields['feedback'].label = 'الملاحظات'
        return form

    class Meta:
        verbose_name = 'تقييم ولي أمر لكورس'
        verbose_name_plural = 'تقييمات أولياء الأمور للكورسات'

    # Excel export configuration
    excel_filename = 'parent_course_ratings'
