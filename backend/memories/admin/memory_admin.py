#!/usr/bin/env python3
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from core.utils import ExcelExportMixin
from memories.models import Memory

@admin.register(Memory)
class MemoryAdmin(ExcelExportMixin, admin.ModelAdmin):
    excel_filename = 'memories'
    list_display = [
        'action_checkbox',
        'media_type',
        'uploader_name',
        'children_count',
        'students_count',
        'is_active',
        'image_preview',
        'created_at'
    ]
    list_filter = ['media_type', 'is_active', 'created_at']
    search_fields = [
        'caption',
        'uploaded_by__user__first_name',
        'uploaded_by__user__last_name',
        'children__first_name',
        'children__last_name',
        'children__unique_code',
        'students__user__first_name',
        'students__user__last_name',
        'students__unique_code',
    ]
    readonly_fields = ['image_preview_large', 'created_at', 'updated_at']
    autocomplete_fields = ['children', 'students', 'uploaded_by']
    list_per_page = 25
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('uploaded_by', 'uploaded_by__user').prefetch_related('children', 'students')
        
    @admin.display(description=_('المشرف رافع الذكرى'))
    def uploader_name(self, obj):
        return obj.uploaded_by.user.get_full_name()
        
    @admin.display(description=_('عدد الأطفال'))
    def children_count(self, obj):
        return obj.children.count()
        
    @admin.display(description=_('عدد الطلاب'))
    def students_count(self, obj):
        return obj.students.count()

    @admin.display(description=_('معاينة'))
    def image_preview(self, obj):
        url = obj.thumbnail_url
        if url:
            # We add a play button overlay if it's a video
            overlay = ""
            if obj.media_type == Memory.MediaType.VIDEO:
                overlay = '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.5); border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;"><div style="width: 0; height: 0; border-top: 5px solid transparent; border-left: 8px solid white; border-bottom: 5px solid transparent; margin-left: 3px;"></div></div>'
            
            return format_html(
                '<div style="position: relative; display: inline-block; width: 60px; height: 60px;">'
                '<img src="{}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 4px;" />'
                '{}</div>',
                url, format_html(overlay) if overlay else ""
            )
        return '-'

    @admin.display(description=_('معاينة كبيرة'))
    def image_preview_large(self, obj):
        url = obj.thumbnail_url
        if url:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; object-fit: cover; border-radius: 8px;" />',
                url
            )
        return '-'
