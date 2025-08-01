import requests
import json

API_URL = "http://127.0.0.1:8000/context/recommend/"

def test_new_user():
    # 模擬新用戶，user_id=9999 假設不存在偏好紀錄
    payload = {
        "user_id": 9999,
        "message": "現在推薦吃什麼",
        "location": {"lat": 25.0330, "lng": 121.5654}
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(API_URL, data=json.dumps(payload), headers=headers)
    print("=== 新用戶推薦 ===")
    print(f"狀態碼: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_user_with_preference():
    # 模擬有偏好用戶（假設 user_id=2，偏好內含「甜點」）
    payload = {
        "user_id": 2,
        "message": "現在推薦吃什麼",
        "location": {"lat": 25.0330, "lng": 121.5654}
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(API_URL, data=json.dumps(payload), headers=headers)
    print("=== 有偏好用戶推薦 ===")
    print(f"狀態碼: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_new_user()
    test_user_with_preference()