# account_app/urls.py 
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.records.urls')),  
    path('accounts/', include('django.contrib.auth.urls')), 
    path('accounts/', include('apps.accounts.urls')), 
    path('', include('apps.reports.urls')),  

]

  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"