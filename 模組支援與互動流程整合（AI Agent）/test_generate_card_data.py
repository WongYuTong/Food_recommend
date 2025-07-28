import requests

# 測試 API 的 URL
url = "http://localhost:8000/agent/generate_card_data/"

# 測試輸入資料
test_input = {
    "restaurants": [
        {"name": "小確幸甜點店", "rating": 4.6, "address": "台北市大安區忠孝東路"},
        {"name": "阿牛燒肉", "rating": 4.2, "address": "新北市板橋區文化路"},
        {"name": "健康素食坊", "rating": 4.8, "address": "台中市西區健行路"},
        {"name": "宵夜拉麵", "rating": 4.4, "address": "台北市信義區松壽路"},
        {"name": "老王牛肉麵", "rating": 3.9, "address": "桃園市中壢區中正路"},
        {"name": "陽光咖啡館", "rating": 4.9, "address": "台北市中山區林森北路"},
    ]
}

try:
    response = requests.post(url, json=test_input)
    print("狀態碼:", response.status_code)
    print("回應內容:")
    for r in response.json().get("results", []):
        print(r)
except requests.exceptions.ConnectionError:
    print("❌ 無法連線到 API，請確認 Django server 是否啟動，且路由正確。")