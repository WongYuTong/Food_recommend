import os
import django
import json
import requests

# 設定 Django 環境變數
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_recommendation_system.settings')
django.setup()

TEST_USER_ID = 6

def call_delete_preference_api(user_id, sentence):
    """
    直接將整句話傳給 API，由 views.py 判斷刪除意圖與要刪除的項目。
    """
    url = "http://127.0.0.1:8000/context/delete_preference_item/"
    payload = {"user_id": user_id, "sentence": sentence}  # 這裡改成 sentence
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    try:
        return response.status_code, response.json()
    except Exception:
        return response.status_code, {"error": "無法解析回應"}

def main():
    sentence = "我不要牛肉"  # 直接設定測試語句
    status_code, result = call_delete_preference_api(TEST_USER_ID, sentence)
    if status_code == 200:
        print(f"✅ {result.get('message', '已成功刪除偏好')}")
    else:
        print(f"❌ 錯誤 ({status_code}): {result}")

if __name__ == "__main__":
    main()