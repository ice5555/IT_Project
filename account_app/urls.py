# account_app/urls.py 
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.records.urls')),  # 将所有应用的路由包含进来
    path('accounts/', include('django.contrib.auth.urls')),  # 添加这一行
    path('accounts/', include('apps.accounts.urls')),  # 更新这里
    path('', include('apps.reports.urls')),  # 将所有应用的路由包含进来

]
