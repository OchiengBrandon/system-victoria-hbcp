import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'victoria.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_superuser(email, password):
    User = get_user_model()
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(email=email, password=password)
        print(f'Superuser with email {email} created successfully.')
    else:
        print(f'Superuser with email {email} already exists.')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python create_superuser.py <email> <password>")
    else:
        email, password = sys.argv[1], sys.argv[2]
        create_superuser(email, password)