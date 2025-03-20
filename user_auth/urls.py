# apps/user_auth/urls.py

from django.urls import path
from django.contrib.auth.views import LogoutView, LoginView

from .views import register

app_name = 'user_auth'  # 添加命名空间

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]