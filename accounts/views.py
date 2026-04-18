from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import CitizenSignupForm

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if hasattr(user, 'role'):
                if user.role == 'citizen':
                    return redirect('citizen_dashboard')
                elif user.role == 'worker':
                    return redirect('worker_dashboard')
            
            if user.is_superuser:
                return redirect('/admin/')
        else:
            messages.error(request, "Username or password is in correct")

    return render(request, 'accounts/login.html')

def signup(request):
    if request.method == 'POST':
        form = CitizenSignupForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'citizen'
            user.phone_number = request.POST.get('phone_number')
            user.auto_location = request.POST.get('auto_location')
            user.save()

            login(request, user)
            return redirect('citizen_dashboard')
        else:
            # Check for specific errors like password length
            for field, errors in form.errors.items():
                for error in errors:
                    if "short" in error.lower() or "too short" in error.lower():
                        messages.warning(request, "Short password not accepted")
                    else:
                        messages.error(request, f"{field.title()}: {error}")
    else:
        form = CitizenSignupForm()

    return render(request, 'accounts/signup.html', {'form': form})
