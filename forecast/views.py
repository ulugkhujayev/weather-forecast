import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.db.models import Sum
from django.conf import settings
from .models import SearchHistory


def index(request):
    last_city = None
    if request.user.is_authenticated:
        last_search = (
            SearchHistory.objects.filter(user=request.user)
            .order_by("-last_searched")
            .first()
        )
        if last_search:
            last_city = last_search.city_name
    return render(request, "forecast/index.html", {"last_city": last_city})


@require_http_methods(["GET"])
def city_autocomplete(request):
    query = request.GET.get("q", "")
    api_key = settings.OPENWEATHERMAP_API_KEY
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=5&appid={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        cities = response.json()
        data = [
            {
                "name": f"{city['name']}, {city.get('state', '')}, {city['country']}",
                "lat": city["lat"],
                "lon": city["lon"],
            }
            for city in cities
        ]
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse([], safe=False)


@require_http_methods(["GET"])
def get_weather(request):
    city_name = request.GET.get("city", "")
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not all([city_name, lat, lon]):
        return JsonResponse({"error": "Missing city information"}, status=400)

    cache_key = f"weather_{city_name}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        cache.set(cache_key, data, 3600)  # Cache for 1 hour

        if request.user.is_authenticated:
            search_history, created = SearchHistory.objects.get_or_create(
                user=request.user, city_name=city_name
            )
            if not created:
                search_history.count += 1
                search_history.save()

        return JsonResponse(data)
    else:
        return JsonResponse({"error": "Failed to fetch weather data"}, status=500)


@require_http_methods(["GET"])
def search_history(request):
    if request.user.is_authenticated:
        history = SearchHistory.objects.filter(user=request.user).order_by("-count")
        data = [{"city": h.city_name, "count": h.count} for h in history]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


@require_http_methods(["GET"])
def city_search_stats(request):
    stats = (
        SearchHistory.objects.values("city_name")
        .annotate(total_count=Sum("count"))
        .order_by("-total_count")
    )
    return JsonResponse(list(stats), safe=False)


@require_http_methods(["GET"])
def city_search_stats(request):
    stats = (
        SearchHistory.objects.values("city_name")
        .annotate(total_count=Sum("count"))
        .order_by("-total_count")
    )
    return JsonResponse(list(stats), safe=False)


@require_http_methods(["GET"])
def api_city_search_stats(request):
    stats = (
        SearchHistory.objects.values("city_name")
        .annotate(total_count=Sum("count"))
        .order_by("-total_count")
    )
    return JsonResponse(
        {
            "city_stats": list(stats),
            "total_searches": sum(stat["total_count"] for stat in stats),
        }
    )
