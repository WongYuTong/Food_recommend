import os
import django
import json
import requests

# 設定 Django 環境變數
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_recommendation_system.settings')
django.setup()

TEST_USER_ID = 3

def has_delete_intent(text):
    return any(kw in text for kw in ["不喜歡", "不要", "不想吃", "刪掉", "移除", "取消"])

def extract_item(text):
    delete_keywords = ["不喜歡", "不要", "不想吃", "刪掉", "移除", "取消"]
    for kw in delete_keywords:
        if kw in text:
            return text.split(kw)[-1].strip()
    return None

def call_delete_preference_api(user_id, item):
    # 修正這裡，改成與 urls.py 一致的路徑
    url = "http://127.0.0.1:8000/context/delete_preference_item/"
    payload = {"user_id": user_id, "item": item}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    try:
        return response.status_code, response.json()
    except Exception:
        return response.status_code, {"error": "無法解析回應"}

def main():
    user_input = input("請輸入語句（例如：我不要牛肉）：\n")

    if not has_delete_intent(user_input):
        print("⚠️ 未偵測到刪除偏好意圖。請輸入包含「不要、刪掉、不喜歡」等字眼的句子。")
        return

    item = extract_item(user_input)
    if not item:
        print("⚠️ 未能抽出要刪除的偏好項目。")
        return

    status_code, result = call_delete_preference_api(TEST_USER_ID, item)
    if status_code == 200:
        print(f"✅ {result.get('message', '已刪除')}")
    else:
        print(f"❌ 錯誤 ({status_code}): {result}")

if __name__ == "__main__":
    main()