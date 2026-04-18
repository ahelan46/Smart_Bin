from django.urls import path
from .views import my_complaints, worker_dashboard, update_status, admin_dashboard

from .views import leaderboard
from .views import citizen_dashboard
from . import views

urlpatterns = [
    path('worker/', worker_dashboard, name='worker_dashboard'),
    path('update/<uuid:complaint_id>/', update_status, name='update_status'),
    path('leaderboard/', leaderboard, name='leaderboard'),
    path('citizen/', citizen_dashboard, name='citizen_dashboard'),
    path('my-complaints/', my_complaints, name='my_complaints'),
    path('complaint/delete/<int:complaint_id>/', views.delete_complaint, name='delete_complaint'),
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    
    # Notification API
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
]


