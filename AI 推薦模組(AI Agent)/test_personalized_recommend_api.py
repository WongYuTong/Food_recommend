import os
import django
import json
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_recommendation_system.settings')
django.setup()

TEST_USER_ID = 2

def test_recommend_restaurant():
    url = "http://127.0.0.1:8000/context/recommend/"
    payload = {
        "user_id": TEST_USER_ID,
        "message": "今天想推薦一些美食",
        "location": {"lat": 25.0330, "lng": 121.5654}
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_recommend_restaurant()