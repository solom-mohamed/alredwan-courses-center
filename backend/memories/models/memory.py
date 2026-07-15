#!/usr/bin/env python3
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from cloudinary.models import CloudinaryField


class Memory(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", _("صورة")
        VIDEO = "video", _("فيديو")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
        verbose_name=_("نوع الوسائط")
    )
    
    file = CloudinaryField(
        folder='memories/',
        resource_type='auto',
        transformation={
            'quality': 'auto',
            'fetch_format': 'auto',
        },
        verbose_name=_("الملف")
    )
    
    caption = models.TextField(blank=True, default='', verbose_name=_("التعليق"))
    
    children = models.ManyToManyField(
        'parents.Child',
        related_name='memories',
        blank=True,
        verbose_name=_("الأطفال")
    )
    
    students = models.ManyToManyField(
        'users.StudentUser',
        related_name='memories',
        blank=True,
        verbose_name=_("الطلاب")
    )
    
    uploaded_by = models.ForeignKey(
        'users.Instructor',
        on_delete=models.PROTECT,
        related_name='uploaded_memories',
        verbose_name=_("تم الرفع بواسطة")
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_("نشط"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))

    class Meta:
        app_label = 'memories'
        verbose_name = _("ذكرى")
        verbose_name_plural = _("الذكريات")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_media_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')} بواسطة {self.uploaded_by.user.get_full_name()}"

    def can_edit(self, user):
        """
        Check if the given user can edit/delete this memory.
        - Admins can always edit.
        - The uploading supervisor can edit within 24 hours of creation.
        """
        if getattr(user, 'role', None) == 'admin':
            return True
            
        if hasattr(user, 'instructor_profile') and user.instructor_profile == self.uploaded_by:
            time_diff = timezone.now() - self.created_at
            return time_diff <= timedelta(hours=24)
            
        return False
        
    @property
    def thumbnail_url(self):
        """Build thumbnail URL depending on media type"""
        if not self.file:
            return None
            
        public_id = getattr(self.file, 'public_id', self.file) if self.file else None
        if not public_id:
            return None
            
        if self.media_type == self.MediaType.IMAGE:
            from core.utils.cloudinary import get_optimized_url
            return get_optimized_url(public_id, width=400, height=400, crop='fill')
            
        elif self.media_type == self.MediaType.VIDEO:
            import cloudinary
            return cloudinary.CloudinaryVideo(public_id).build_url(
                width=400, 
                height=400, 
                crop='fill',
                resource_type='video',
                format='jpg' # Auto-generates a frame for the video thumbnail
            )
        return None
