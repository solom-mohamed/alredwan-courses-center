import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Redwan_courses_center.settings')
django.setup()

import cloudinary.uploader
try:
    res = cloudinary.uploader.upload('manage.py', resource_type='raw')
    print('SUCCESS:', res['secure_url'])
except Exception as e:
    print('ERROR:', str(e))
