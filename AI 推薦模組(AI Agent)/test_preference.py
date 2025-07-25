import os
import django
import json
import requests

# 設定 Django 環境變數
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_recommendation_system.settings')
django.setup()

# 測試用 User ID（依資料庫實際使用者 ID 調整）
TEST_USER_ID = 1

def test_save_user_preference():
    url = "http://127.0.0.1:8000/context/save_preference/"

    payload = {
        "user_id": TEST_USER_ID,
        "preferences": "我喜歡吃雞肉和牛肉，不喜歡海鮮"
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"Save Preference: {response.status_code} {response.json()}")

def test_get_user_preference():
    url = f"http://127.0.0.1:8000/context/get_preference/?user_id={TEST_USER_ID}"

    response = requests.get(url)
    print(f"Get Preference: {response.status_code} {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_save_user_preference()
    test_get_user_preference()