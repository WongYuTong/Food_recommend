import os
import django
import requests
import json

# ---------------------- Django 環境 ----------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_recommendation_system.settings')
django.setup()  # 先 setup

# ---------------------- 測試設定 ----------------------
USER_ID = 24  # 直接使用已存在的使用者 ID
BASE_URL = "http://127.0.0.1:8000/context/"
HEADERS = {"Content-Type": "application/json"}

# ---------------------- 聊天測試主程式 ----------------------
def chat_loop():
    print("=== 餐廳推薦系統測試 ===")
    print("輸入 'exit' 離開對話")

    while True:
        user_input = input("\n請輸入訊息：")
        if user_input.lower() == "exit":
            print("結束對話")
            break

        # ---- 刪除偏好 ----
        if user_input.lower().startswith("delete "):
            sentence = user_input[7:].strip()
            try:
                r = requests.post(
                    BASE_URL + "delete_preference_item/",
                    json={"user_id": USER_ID, "sentence": sentence},
                    headers=HEADERS
                )
                try:
                    data = r.json()
                    print(f"刪除偏好回傳: {r.status_code},\n{json.dumps(data, ensure_ascii=False, indent=2)}")
                except:
                    print(f"刪除偏好回傳: {r.status_code}, {r.text}")
            except Exception as e:
                print(f"刪除偏好時發生錯誤: {e}")
            continue

        # ---- 儲存偏好 ----
        try:
            r = requests.post(
                BASE_URL + "save_preference/",
                json={"user_id": USER_ID, "preferences": user_input},
                headers=HEADERS
            )
            try:
                data = r.json()
                print(f"儲存偏好回傳: {r.status_code},\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            except:
                print(f"儲存偏好回傳: {r.status_code}, {r.text}")
        except Exception as e:
            print(f"儲存偏好時發生錯誤: {e}")

        # ---- 取得推薦 ----
        try:
            r = requests.post(
                BASE_URL + "recommend/",
                json={
                    "user_id": USER_ID,
                    "message": user_input,
                    "location": {"lat": 25.0330, "lng": 121.5654}
                },
                headers=HEADERS
            )
            try:
                data = r.json()
                print(f"推薦回傳: {r.status_code},\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            except:
                print(f"推薦回傳: {r.status_code}, {r.text}")
        except Exception as e:
            print(f"取得推薦時發生錯誤: {e}")

if __name__ == "__main__":
    chat_loop()