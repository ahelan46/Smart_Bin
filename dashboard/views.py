from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from complaints.models import Complaint, SystemSettings
from complaints.notifications import send_status_notification
from django.contrib.auth.decorators import login_required
import base64
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.utils import timezone

@login_required
def citizen_dashboard(request):
    if request.user.role != 'citizen':
        return redirect('login')

    complaints = Complaint.objects.filter(user=request.user)

    context = {
        'complaints': complaints,
        'total_complaints': complaints.count(),
        'cleaned_count': complaints.filter(status='cleaned').count(),
        'pending_count': complaints.exclude(status='cleaned').count(),
    }

    return render(request, 'dashboard/citizen_dashboard.html', context)

def calculate_level(complaints_count):
    """
    Calculates the level based on the number of completed complaints.
    """
    # Define the ranges: (start_level, end_level, complaints_per_level)
    tiers = [
        (1, 5, 2), (6, 10, 5), (11, 20, 10), (21, 30, 15), (31, 50, 20),
        (51, 65, 30), (66, 75, 50), (76, 80, 80), (81, 90, 100), (91, 95, 1000),
        (96, 100, 10000), (101, 120, 100000), (121, 130, 100000),
        (131, 140, 10000000), (141, 150, 10000000000000000000)
    ]
    
    total_needed = 0
    current_level = 1
    
    for start, end, per_level in tiers:
        levels_in_tier = (end - start) + 1
        complaints_in_tier = levels_in_tier * per_level
        
        if complaints_count >= total_needed + complaints_in_tier:
            total_needed += complaints_in_tier
            current_level = end + 1 # Move to next tier
        else:
            # User is within this tier
            remaining = complaints_count - total_needed
            level_gain = remaining // per_level
            current_level = start + level_gain
            break
            
    return min(current_level, 150) # Cap at level 150

@login_required
def like_user(request, user_id):
    target_user = get_object_or_404(CustomUser, id=user_id)
    if request.user in target_user.likes.all():
        target_user.likes.remove(request.user) # Unlike if already liked
        liked = False
    else:
        target_user.likes.add(request.user) # Add like
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'total_likes': target_user.total_likes
    })

def leaderboard(request):
    # Fetch users and their complaint counts
    # We use points as the sorting metric (assuming 1 complaint = 10 points)
    users_list = CustomUser.objects.filter(role='citizen').order_by('-points')
    
    ranked_users = []
    current_rank = 0
    prev_points = None
    
    for user in users_list:
        user.complaint_count = Complaint.objects.filter(user=user, status='cleaned').count()
        
    for i, user in enumerate(users_list):
        # 1. Rank Calculation
        if user.points != prev_points:
            current_rank = i + 1
        user.display_rank = current_rank
        
        # 2. Level Calculation 
        # (Assuming 10 points = 1 cleaned complaint based on your update_status view)
        complaint_count = user.points // 5
        user.level = calculate_level(complaint_count)
        
        # 3. Badge Logic (Top 3 ranks)
        if current_rank == 1:
            user.dynamic_badge = "Gold"
        elif current_rank == 2:
            user.dynamic_badge = "Silver"
        elif current_rank == 3:
            user.dynamic_badge = "Bronze"
        else:
            user.dynamic_badge = None
            
        prev_points = user.points
        ranked_users.append(user)

    return render(request, 'dashboard/leaderboard.html', {'users': ranked_users})

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            return redirect('submit_complaint')
        return view_func(request, *args, **kwargs)
    return wrapper

def worker_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'worker':
            return redirect('submit_complaint')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@worker_required
def worker_dashboard(request):
    settings = SystemSettings.get_settings()
    visible_area = settings.visible_area
    
    complaints = Complaint.objects.filter(status__in=['pending', 'verified', 'in_progress'])
    
    if visible_area == 'public':
        complaints = complaints.filter(area_type='public')
    elif visible_area == 'private':
        complaints = complaints.filter(area_type='private')
    
    complaints = complaints.order_by('-created_at')
    
    return render(request, 'dashboard/worker_dashboard.html', {
        'complaints': complaints,
        'visible_area': visible_area
    })

@login_required
@admin_required
def admin_dashboard(request):
    settings = SystemSettings.get_settings()
    
    if request.method == "POST":
        visible_area = request.POST.get("visible_area")
        if visible_area in ['public', 'private', 'both']:
            settings.visible_area = visible_area
            settings.save()
            return redirect('admin_dashboard')

    return render(request, 'dashboard/admin_dashboard.html', {'sys_settings': settings})


@login_required
@worker_required
def update_status(request, complaint_id):
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        
        if new_status == "cleaned":
            complaint.status = "cleaned"
            complaint.cleaned_at = timezone.now()
            
            # Handle the Captured Photo (Base64)
            image_data = request.POST.get("cleaned_image_data")
            if image_data and "base64," in image_data:
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f"cleaned_{complaint_id}.{ext}")
                complaint.cleaned_image.save(data.name, data, save=False)

            # Badge/Points logic (Shared ranks)
            reporting_user = complaint.user
            reporting_user.points += 5  # Award 5 points per cleaned complaint
            reporting_user.save()

            # Recalculate Badges for top 3 unique points
            top_points = CustomUser.objects.filter(role='citizen').values_list('points', flat=True).distinct().order_by('-points')[:3]
            point_list = list(top_points)
            CustomUser.objects.filter(role='citizen').update(badge="")
            if len(point_list) >= 1: CustomUser.objects.filter(role='citizen', points=point_list[0]).update(badge="Gold")
            if len(point_list) >= 2: CustomUser.objects.filter(role='citizen', points=point_list[1]).update(badge="Silver")
            if len(point_list) >= 3: CustomUser.objects.filter(role='citizen', points=point_list[2]).update(badge="Bronze")

        else:
            complaint.status = new_status

        complaint.save()
        
        # Trigger notification
        send_status_notification(complaint)

    return redirect('worker_dashboard')
@login_required
def my_complaints(request):
    if request.user.role != 'citizen':
        return redirect('login')

    complaints = Complaint.objects.filter(user=request.user)

    return render(request, 'dashboard/my_complaints.html', {
        'complaints': complaints
    })

@login_required
def delete_complaint(request, complaint_id):
    if request.method == 'POST':
        # Get the complaint, ensuring it belongs to the logged-in user
        complaint = get_object_or_404(Complaint, id=complaint_id, user=request.user)
        complaint.delete()
    return redirect('my_complaints')
@login_required
def get_notifications(request):
    """
    Returns unread notifications for the logged-in user as JSON.
    """
    from complaints.models import Notification
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    data = [
        {
            'id': n.id,
            'message': n.message,
            'status_type': n.status_type,
            'created_at': n.created_at.strftime("%I:%M %p"),
            'title': n.get_status_type_display()
        }
        for n in notifications
    ]
    return JsonResponse({'notifications': data})

@login_required
def mark_notification_read(request, notification_id):
    """
    Marks a specific notification as read.
    """
    from complaints.models import Notification
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})
