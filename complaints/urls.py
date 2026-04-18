from django.urls import path
from .views import submit_complaint
from .views import complaints_map

urlpatterns = [
    path('submit/', submit_complaint, name='submit_complaint'),
    path('map/', complaints_map, name='complaints_map'),
]
