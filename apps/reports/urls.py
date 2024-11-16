from django.shortcuts import render
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import overview_charts
# Create your views here.
urlpatterns = [
    # ... 之前的路径
    path('overview-charts/', overview_charts, name='overview_charts'),
    # ...
]