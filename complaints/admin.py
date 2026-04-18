from django.contrib import admin
from .models import Complaint, SystemSettings

admin.site.register(Complaint)
admin.site.register(SystemSettings)
