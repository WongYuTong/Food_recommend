import requests

url = "http://localhost:8000/agent/generate_recommend_reasons/"
data = {
    "restaurants": [
        {
            "name": "這一小鍋 台北車站店",
            "rating": 4.8,
            "address": "台北市中正區忠孝西路",
            "is_open": True,
            "highlight": "甜點評價高",
            "matched_tags": ["火鍋", "高評價"],
            "distance": "400 公尺",
            "reason_score": 0.92
        },
        {
            "name": "某某燒肉店",
            "rating": 4.2,
            "address": "台北市信義區",
            "is_open": False,
            "highlight": "氣氛佳",
            "matched_tags": ["燒肉"],
            "distance": "800 公尺",
            "reason_score": 0.75
        },
        {
            "name": "隨便吃吃",
            "rating": 3.8,
            "address": "新北市板橋區",
            "is_open": None,  # 測試「無資料」狀況
            "matched_tags": [],
            "distance": "600 公尺"
        }
    ]
}

response = requests.post(url, json=data)
print("狀態碼:", response.status_code)
print("回應內容:")
print(response.json())