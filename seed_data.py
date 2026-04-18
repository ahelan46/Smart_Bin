import os
import django
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
import random

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import CustomUser
from complaints.models import Complaint

def seed_data():
    print("Starting data seeding...")

    # 1. Create Users
    users_data = [
        {'username': 'citizen_joe', 'role': 'citizen', 'points': 150, 'badge': 'Eco Warrior'},
        {'username': 'citizen_jane', 'role': 'citizen', 'points': 75, 'badge': 'Green Scout'},
        {'username': 'worker_sam', 'role': 'worker', 'points': 0, 'badge': None},
    ]

    users = []
    for u_data in users_data:
        user, created = CustomUser.objects.get_or_create(
            username=u_data['username'],
            defaults={
                'role': u_data['role'],
                'points': u_data['points'],
                'badge': u_data['badge']
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            print(f"Created user: {user.username}")
        else:
            print(f"User {user.username} already exists.")
        users.append(user)

    # 2. Create Complaints
    # Small red dot base64
    img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    image_data = base64.b64decode(img_b64)
    
    complaints_data = [
        {
            'user': 'citizen_joe',
            'latitude': 12.9716,
            'longitude': 77.5946,
            'description': 'Large pile of plastic near the park entrance.',
            'status': 'pending',
            'severity': 'high',
            'location_name': 'Kuberan Park, Bangalore'
        },
        {
            'user': 'citizen_joe',
            'latitude': 12.9800,
            'longitude': 77.6000,
            'description': 'Overflowing bin near the bus stop.',
            'status': 'cleaned',
            'severity': 'moderate',
            'location_name': 'MG Road Bus Stand, Bangalore',
            'cleaned_at': timezone.now()
        },
        {
            'user': 'citizen_jane',
            'latitude': 12.9500,
            'longitude': 77.5800,
            'description': 'Scattered waste on the sidewalk.',
            'status': 'verified',
            'severity': 'low',
            'location_name': 'Lalbagh West Gate, Bangalore'
        },
    ]

    for c_data in complaints_data:
        user = CustomUser.objects.get(username=c_data['user'])
        
        # Avoid creating the exact same complaint twice if running script multiple times
        if not Complaint.objects.filter(description=c_data['description'], user=user).exists():
            complaint = Complaint(
                user=user,
                latitude=c_data['latitude'],
                longitude=c_data['longitude'],
                description=c_data['description'],
                status=c_data['status'],
                severity=c_data.get('severity'),
                location_name=c_data['location_name'],
                cleaned_at=c_data.get('cleaned_at')
            )
            
            image_name = f"seed_{random.randint(1000, 9999)}.png"
            complaint.image.save(image_name, ContentFile(image_data), save=False)
            complaint.save()
            print(f"Created complaint: {c_data['description'][:30]}...")
        else:
            print(f"Complaint already exists: {c_data['description'][:30]}...")

    print("Data seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
