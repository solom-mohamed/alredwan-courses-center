"""
URL configuration for Redwan_courses_center project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from core.views import health_check, font_diagnostic
from django.conf import settings
from django.conf.urls.static import static


admin.site.site_header = "لوحة إدارة واحة الرضوان"
admin.site.site_title = "واحة الرضوان"
admin.site.index_title = "الصفحة الرئيسية"
urlpatterns = [
    path('Al-Redwan-superadmin-dashboard/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('api/diagnostics/fonts/', font_diagnostic, name='font_diagnostic'),
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.jwt')),
    path('api/courses/', include('courses.urls')),
    path('api/users/', include('users.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/', include('enrollments_payments.urls')),
    path('api/parents/', include('parents.urls')),
    path('api/memories/', include('memories.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
