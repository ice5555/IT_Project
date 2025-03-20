# apps/accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views 
from .views import register

app_name = 'accounts'  # 添加命名空间

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),

]