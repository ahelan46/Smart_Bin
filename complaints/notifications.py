from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
import logging

logger = logging.getLogger(__name__)

def send_status_notification(complaint):
    """
    Saves a 'Mission Alert' notification in the database for the user.
    Email and SMS alerts are disabled as per user request.
    """
    user = complaint.user
    status = complaint.status
    
    # Map status to user-friendly messages for "Mission Alerts"
    status_messages = {
        'verified': {
            'title': 'Mission Accepted 🚀',
            'msg': f'Your complaint at {complaint.location_name or "marked location"} has been verified! Cleaning will start soon.'
        },
        'in_progress': {
            'title': 'Mission In Progress 🧹',
            'msg': f'A worker is currently cleaning up the garbage at {complaint.location_name or "marked location"}.'
        },
        'cleaned': {
            'title': 'Mission Completed ✅',
            'msg': f'Great news! The garbage at {complaint.location_name or "marked location"} has been cleared. Thank you!'
        }
    }

    if status in status_messages:
        msg_data = status_messages[status]
        
        # Save to Database for In-App "Mission Alert" UI
        Notification.objects.create(
            user=user,
            complaint=complaint,
            message=msg_data['msg'],
            status_type=status,
        )
        logger.info(f"Mission Alert saved for {user.username}: {status}")
        
        # Email and SMS are now DISABLED as per user request
        # _send_email_notification(user, msg_data['title'], msg_data['msg'])
        # _send_sms_notification(user, msg_data['msg'])

def _send_email_notification(user, subject, message):
    # DISABLED: Alerts are now handled via in-app Mission Alerts
    pass

def _send_sms_notification(user, message):
    # DISABLED: Alerts are now handled via in-app Mission Alerts
    pass
