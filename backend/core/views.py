from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# Create your views here.

def health_check(request):
    """
    Simple health check endpoint. 
    Returns 200 OK with a JSON response to confirm the server is running.
    """
    return JsonResponse({"status": "ok"})


@require_http_methods(["GET"])
def font_diagnostic(request):
    """
    Diagnostic endpoint to check Arabic font installation status.
    Access at /api/diagnostics/fonts/ to verify fonts are working in production.
    """
    from core.utils.font_utils import verify_font_installation
    import sys
    import os
    
    status = verify_font_installation()
    
    # Add system information
    status['system_info'] = {
        'python_version': sys.version,
        'platform': sys.platform,
        'environment': os.getenv('DJANGO_SETTINGS_MODULE', 'unknown'),
    }
    
    # Check for common font directories
    font_dirs = [
        '/usr/share/fonts/truetype/dejavu',
        '/usr/share/fonts/truetype/noto',
        '/usr/share/fonts',
        'C:\\Windows\\Fonts',
    ]
    
    status['font_directories'] = {}
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            try:
                files = os.listdir(font_dir)
                ttf_files = [f for f in files if f.endswith('.ttf')]
                status['font_directories'][font_dir] = {
                    'exists': True,
                    'ttf_count': len(ttf_files),
                    'sample_fonts': ttf_files[:5] if ttf_files else []
                }
            except Exception as e:
                status['font_directories'][font_dir] = {
                    'exists': True,
                    'error': str(e)
                }
        else:
            status['font_directories'][font_dir] = {'exists': False}
    
    return JsonResponse(status, json_dumps_params={'ensure_ascii': False, 'indent': 2})

# ---------------------------------------------------------------------------
# Landing page videos
# ---------------------------------------------------------------------------
from rest_framework import generics  # noqa: E402
from rest_framework.permissions import AllowAny  # noqa: E402

from .models import LandingVideo  # noqa: E402
from .serializers import LandingVideoSerializer  # noqa: E402


class LandingVideoListView(generics.ListAPIView):
    """Public list of the active landing page clips, in display order.

    GET /api/landing/videos/
    """
    permission_classes = [AllowAny]
    serializer_class = LandingVideoSerializer
    pagination_class = None

    def get_queryset(self):
        return LandingVideo.objects.filter(is_active=True)
