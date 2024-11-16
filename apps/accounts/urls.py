# apps/accounts/urls.py

from django.urls import path
from .views import register

app_name = 'accounts'  # 添加命名空间

urlpatterns = [
    path('register/', register, name='register'),
    # 其他认证相关的路由
]