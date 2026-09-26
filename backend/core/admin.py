from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import LandingVideo


@admin.register(LandingVideo)
class LandingVideoAdmin(admin.ModelAdmin):
    """Manage the clips of the landing page reel; reorder from the list."""
    list_display = ('title', 'get_source', 'get_duration', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('order', '-created_at')
    save_on_top = True
    fieldsets = (
        (_("المحتوى"), {'fields': ('title', 'description', 'poster')}),
        (_("الفيديو"), {
            'fields': ('video_url', 'video_file', 'duration_seconds'),
            'description': _("الصق رابط YouTube/Vimeo/Bunny أو رابط mp4، أو ارفع ملف فيديو. الملف المرفوع له الأولوية."),
        }),
        (_("العرض"), {'fields': (('order', 'is_active'),)}),
    )

    @admin.display(description=_("المصدر"))
    def get_source(self, obj):
        return obj.get_source_display() if hasattr(obj, 'get_source_display') else dict(LandingVideo.Source.choices)[obj.source]

    @admin.display(description=_("المدة"))
    def get_duration(self, obj):
        minutes, seconds = divmod(obj.duration_seconds or 0, 60)
        return f"{minutes}:{seconds:02d}"
