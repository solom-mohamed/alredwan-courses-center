from cloudinary.models import CloudinaryField
from cloudinary.utils import cloudinary_url
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class LandingVideo(models.Model):
    """A short clip shown in the landing page's "شاهد الواحة عن قرب" reel.

    Either paste a link (YouTube / Vimeo / Bunny or a direct .mp4) or upload a
    file to Cloudinary; the public API always exposes one playable URL.
    """

    class Source(models.TextChoices):
        LINK = 'link', _('رابط (YouTube / Vimeo / Bunny / mp4)')
        UPLOAD = 'upload', _('ملف مرفوع')

    title = models.CharField(max_length=150, verbose_name=_("العنوان"))
    description = models.CharField(max_length=300, blank=True, verbose_name=_("وصف قصير"))
    video_url = models.URLField(
        max_length=500, blank=True, verbose_name=_("رابط الفيديو"),
        help_text=_("YouTube أو Vimeo أو Bunny أو رابط mp4 مباشر. اتركه فارغاً لو رفعت ملفاً."),
    )
    video_file = CloudinaryField(
        _("ملف الفيديو"), resource_type='video', blank=True, null=True,
        folder='landing_videos',
    )
    poster = CloudinaryField(
        _("صورة الغلاف"), blank=True, null=True, folder='landing_videos/posters',
        transformation={'width': 1200, 'crop': 'limit', 'quality': 'auto:good', 'fetch_format': 'auto'},
    )
    duration_seconds = models.PositiveIntegerField(
        default=0, verbose_name=_("المدة بالثواني"),
        help_text=_("تظهر كشارة على الفيديو، مثال 90 = 1:30"),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("الترتيب"))
    is_active = models.BooleanField(default=True, verbose_name=_("ظاهر"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإضافة"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _("فيديو الصفحة الرئيسية")
        verbose_name_plural = _("فيديوهات الصفحة الرئيسية")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if not self.video_url and not self.video_file:
            raise ValidationError(_("أضف رابط فيديو أو ارفع ملف فيديو."))

    @property
    def source(self):
        return self.Source.UPLOAD if self.video_file else self.Source.LINK

    @property
    def playback_url(self):
        """The URL the frontend plays: the uploaded file when present, else the link."""
        if self.video_file:
            url, _options = cloudinary_url(str(self.video_file), resource_type='video')
            return url
        return self.video_url

    @property
    def poster_url(self):
        if not self.poster:
            return None
        return getattr(self.poster, 'url', None) or cloudinary_url(str(self.poster))[0]
