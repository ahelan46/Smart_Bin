from django.urls import path
from .views import signup, user_login
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
