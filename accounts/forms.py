from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CitizenSignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'email', 'age']
        labels = {
            'first_name': 'Full Name'
        }
