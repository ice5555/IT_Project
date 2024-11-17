from django.shortcuts import render
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import overview_charts, income_trend_chart, income_list
# Create your views here.
urlpatterns = [
    # ... 之前的路径
    path('overview-charts/', overview_charts, name='overview_charts'),
    path('api/income-trend/', income_trend_chart, name='income_trend_chart'),

    path('income_list_trend/', income_list, name='income_list_trend'),

    # ...
]