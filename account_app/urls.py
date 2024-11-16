# account_app/urls.py 
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.records.urls')),  # 将所有应用的路由包含进来
]
