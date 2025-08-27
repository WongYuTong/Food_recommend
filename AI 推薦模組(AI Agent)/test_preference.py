import os
import django
import json
import requests

# 設定 Django 環境變數
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_recommendation_system.settings')
django.setup()

from django.contrib.auth.models import User

# 測試用 User ID
TEST_USER_ID = 6

# 確保使用者存在
try:
    user = User.objects.get(id=TEST_USER_ID)
    print(f"使用者已存在: {user.username} (ID={user.id})")
except User.DoesNotExist:
    print(f"使用者 ID={TEST_USER_ID} 不存在，請先建立此使用者")
    exit(1)  # 結束程式，避免 FK 錯誤

def test_save_user_preference():
    # ⚠️ URL 依照你的專案 urls.py 結構調整：
    # 如果在主 urls.py 有 `path("context/", include("context.urls"))`，就用 /context/ 前綴
    # 如果沒有 include，就改成 http://127.0.0.1:8000/save_preference/
    url = "http://127.0.0.1:8000/context/save_preference/"

    payload = {
        "user_id": TEST_USER_ID,
        "preferences": "我喜歡吃豬肉和牛肉，不喜歡海鮮"
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