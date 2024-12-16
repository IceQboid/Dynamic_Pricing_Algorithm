from django.urls import path
from . import views

urlpatterns = [
    path('village-details/', views.get_village_details, name='village_details'),
    path('top5-restaurants/', views.get_top5_restaurants, name='get_top5_restaurants'),
    path('compare-prices/', views.compare_prices, name='compare_prices'),
    path('get-busy-times/', views.get_busy_hours, name='get_busy_hours'),
    path('get-current-weather/', views.get_weather, name='get_weather'),
    path('get_adjusted_prices/', views.get_adjusted_prices, name='adjusted_price'),
    
]

