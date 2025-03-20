# account_app/urls.py 
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.records.urls')),  
    path('user_auth/', include('django.contrib.auth.urls')), 
    path('user_auth/', include('apps.user_auth.urls')), 
    path('', include('apps.reports.urls')),  

]
