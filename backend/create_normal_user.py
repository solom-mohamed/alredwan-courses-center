import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Redwan_courses_center.settings')
django.setup()

from users.models.user import CustomUser

try:
    # Check if exists first to avoid unique constraint errors
    if not CustomUser.objects.filter(phone_number1='+201099999999').exists():
        user = CustomUser.objects.create_user(
            phone_number1='+201099999999',
            password='normalpassword123',
            first_name='Normal',
            last_name='Student',
            dob='2005-01-01',
            gender='male',
            role='student'
        )
        print("SUCCESS: Normal student user created! Phone: +201099999999, Password: normalpassword123")
    else:
        print("SUCCESS: User already exists. Phone: +201099999999, Password: normalpassword123")
except Exception as e:
    print("ERROR:", e)
