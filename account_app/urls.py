# account_app/urls.py 
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('user_auth.urls', namespace='user_auth')),
    path('', include('finance_app.urls', namespace='finance_app')),  # 确保 finance_app 被包含
    path('user_auth/', include('django.contrib.auth.urls')), 


]
