from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class MemoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'memories'
    verbose_name = _('ذكريات المسجد')
