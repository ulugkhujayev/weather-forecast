from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("autocomplete/", views.city_autocomplete, name="city_autocomplete"),
    path("weather/", views.get_weather, name="get_weather"),
    path("history/", views.search_history, name="search_history"),
    path("stats/", views.city_search_stats, name="city_search_stats"),
    path("api/stats/", views.api_city_search_stats, name="api_city_search_stats"),
]
