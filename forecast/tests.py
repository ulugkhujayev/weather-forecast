from django.test import TestCase, Client
from django.urls import reverse
from .models import SearchHistory
from django.contrib.auth.models import User
from unittest.mock import patch


class WeatherForecastTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")

    @patch("forecast.views.requests.get")
    def test_city_autocomplete(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "London", "lat": 51.5074, "lon": -0.1278, "country": "GB"}
        ]

        response = self.client.get(reverse("city_autocomplete"), {"q": "London"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"),
            [{"name": "London, , GB", "lat": 51.5074, "lon": -0.1278}],
        )

    # ... other test methods ...
    def test_index_view(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forecast/index.html")

    @patch("forecast.views.requests.get")
    def test_get_weather(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "daily": {"temperature_2m_max": [20]}
        }
        response = self.client.get(
            reverse("get_weather"),
            {"city": "London", "lat": "51.5074", "lon": "-0.1278"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"),
            {"daily": {"temperature_2m_max": [20]}},
        )

    def test_search_history(self):
        self.client.login(username="testuser", password="12345")
        SearchHistory.objects.create(user=self.user, city_name="London", count=1)
        response = self.client.get(reverse("search_history"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"), [{"city": "London", "count": 1}]
        )

    def test_city_search_stats(self):
        SearchHistory.objects.create(user=self.user, city_name="London", count=1)
        response = self.client.get(reverse("city_search_stats"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"),
            [{"city_name": "London", "total_count": 1}],
        )
