import math
import base64
import requests
import cv2
import numpy as np
import os
from ultralytics import YOLO
from django.conf import settings

from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from .forms import ComplaintForm
from django.contrib.auth.decorators import login_required
from .models import Complaint, SystemSettings

# Initialize YOLO model (yolov8n is lightweight)
MODEL_PATH = os.path.join(settings.BASE_DIR, 'yolov8n.pt')
model = YOLO(MODEL_PATH)

def yolo_garbage_check(image_file):
    """
    Detects waste while strictly excluding living things (humans, pets, birds).
    """
    image_file.seek(0)
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        return False, "Could not decode image."

    # Run YOLOv8 detection
    results = model.predict(img, conf=0.25, verbose=False)
    
    found_living = False
    
    # Class IDs for living creatures
    living_classes = [0, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            if cls_id in living_classes:
                found_living = True
                break
        if found_living:
            break

    if found_living:
        return False, "Living things (human/animal) detected! Please capture ONLY the waste."

    # Check variance to ensure it's not a blank wall
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = np.var(gray)
    
    if variance < 300:
        return False, "No visible waste detected or image is too blurry/plain."

    return True, ""



def get_location_name(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "json",
            "lat": lat,
            "lon": lon,
        }
        headers = {"User-Agent": "smart-bin-app"}

        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()

        return data.get("display_name", "Unknown Location")

    except:
        return "Unknown Location"


def is_duplicate(lat1, lon1):
    # Exclude both cleaned and rejected complaints
    complaints = Complaint.objects.exclude(status__in=['cleaned', 'rejected'])

    for c in complaints:
        # Distance threshold (approx 55 meters)
        distance = ((lat1 - c.latitude)**2 + (lon1 - c.longitude)**2)**0.5
        if distance < 0.00050:
            return True

    return False


@login_required
def submit_complaint(request):
    sys_settings = SystemSettings.get_settings()

    if request.method == 'POST':
        image_data = request.POST.get('image')
        submitted_area = request.POST.get('area_type')

        # ---- ENFORCE AREA RESTRICTION FIRST ----
        if sys_settings.visible_area != 'both' and submitted_area != sys_settings.visible_area:
            return render(request, 'complaints/submit.html', {
                'error': f"Only {sys_settings.get_visible_area_display()} complaints are currently accepted.",
                'sys_settings': sys_settings
            })

        if image_data:
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]

            image_file = ContentFile(base64.b64decode(imgstr), name='complaint.' + ext)

            complaint = ComplaintForm().save(commit=False)
            complaint.user = request.user
            complaint.image = image_file
            complaint.latitude = request.POST.get('latitude')
            complaint.longitude = request.POST.get('longitude')
            lat_str = request.POST.get('latitude')
            lon_str = request.POST.get('longitude')

            # Check if data is missing or empty
            if not image_data or not lat_str or not lon_str:
                return render(request, 'complaints/submit.html', {
                    'error': "Missing information. Ensure camera and location are enabled.",
                    'sys_settings': sys_settings
                })

            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                return render(request, 'complaints/submit.html', {
                    'error': "Invalid location data received.",
                    'sys_settings': sys_settings
                })
            location_name = get_location_name(lat, lon)
            complaint.location_name = location_name

            if is_duplicate(lat, lon):
                return render(request, 'complaints/submit.html', {
                    'error': "This place is already reported.",
                    'sys_settings': sys_settings
                })

            valid_garbage, yolo_error = yolo_garbage_check(image_file)
            if not valid_garbage:
                return render(request, 'complaints/submit.html', {
                    'error': yolo_error,
                    'sys_settings': sys_settings
                })

            image_file.seek(0)
            complaint.location_name = location_name
            complaint.area_type = submitted_area
            complaint.save()

            return redirect('submit_complaint')

    return render(request, 'complaints/submit.html', {'sys_settings': sys_settings})


def complaints_map(request):
    complaints = Complaint.objects.all()
    return render(request, 'complaints/map.html', {'complaints': complaints})