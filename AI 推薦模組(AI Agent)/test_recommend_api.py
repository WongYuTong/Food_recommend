import os
import django
import json
import requests

# 設定 Django 環境變數
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_recommendation_system.settings')  # 將 'myproject' 改為你的專案資料夾名稱

# 初始化 Django
django.setup()

def test_recommend_api():
    url = "http://127.0.0.1:8000/context/recommend/"

    payload = {
        "message": "今天想吃療癒一點的晚餐",
        "location": {"lat": 25.0330, "lng": 121.5654}  # 台北101座標作測試
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"測試 API 時發生錯誤: {str(e)}")

if __name__ == "__main__":
    test_recommend_api()