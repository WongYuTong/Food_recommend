import requests
import json

API_URL = "http://127.0.0.1:8000/context/recommend/"

def test_user_without_preference():
    # 無偏好用戶（user_id=12）
    payload = {
        "user_id": 12,
        "message": "今天推薦吃什麼?",
        "location": {"lat": 25.0330, "lng": 121.5654}
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(API_URL, data=json.dumps(payload), headers=headers)
    print("=== 無偏好用戶推薦 ===")
    print(f"狀態碼: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_user_with_preference():
    # 有偏好用戶（user_id=6，假設偏好內含「豬肉」）
    payload = {
        "user_id": 6,
        "message": "今天推薦吃什麼?",
        "location": {"lat": 25.0330, "lng": 121.5654}
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(API_URL, data=json.dumps(payload), headers=headers)
    print("=== 有偏好用戶推薦 ===")
    print(f"狀態碼: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_user_without_preference()
    test_user_with_preference()