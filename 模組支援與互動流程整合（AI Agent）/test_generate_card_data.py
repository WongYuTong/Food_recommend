import requests

# 測試資料
test_data = {
    "restaurants": [
        {"name": "小確幸甜點店", "rating": 4.6, "address": "台北市大安區忠孝東路"},
        {"name": "阿牛燒肉", "rating": 4.2, "address": "新北市板橋區文化路"},
        {"name": "健康素食坊", "rating": 4.8, "address": "台中市西區健行路"},
        {"name": "宵夜拉麵", "rating": 4.4, "address": "台北市信義區松壽路"},
        {"name": "老王牛肉麵", "rating": 3.9, "address": "桃園市中壢區中正路"},
        {"name": "陽光咖啡館", "rating": 4.9, "address": "台北市中山區林森北路"},
        {"name": "快樂漢堡王", "rating": 4.3, "address": "新北市新莊區中平路"}
    ]
}

url = "http://localhost:8000/agent/generate_card_data/"  # 根據實際 URL 修改

# 發送請求
response = requests.post(url, json=test_data)

# 顯示結果
print("🎯 測試結果")
print("狀態碼:", response.status_code)
print("回應內容:")
if response.status_code == 200:
    for r in response.json().get("results", []):
        print("-" * 50)
        for k, v in r.items():
            print(f"{k}: {v}")
else:
    print(response.text)