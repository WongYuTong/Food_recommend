import requests
import json

url = "http://localhost:8000/agent/generate_recommend_reasons/"

data = {
    "restaurants": [
        {
            "name": "這一小鍋 台北車站店",
            "rating": 4.8,
            "address": "台北市中正區忠孝西路",
            "is_open": True,
            "ai_reason": "",
            "comment_summary": "",
            "highlight": "甜點評價高",
            "matched_tags": ["火鍋", "高評價"],
            "distance": "400 公尺",
            "reason_score": 0.92,
            "price_level": "$$"
        },
        {
            "name": "某某燒肉店",
            "rating": 4.2,
            "address": "台北市信義區松壽路",
            "is_open": False,
            "ai_reason": "",
            "comment_summary": "氣氛佳、座位舒適",
            "highlight": "",
            "matched_tags": ["燒肉"],
            "distance": "800 公尺",
            "reason_score": 0.75,
            "price_level": "$$$"
        },
        {
            "name": "平價小吃店",
            "rating": 3.8,
            "address": "新北市板橋區文化路",
            "is_open": True,
            "ai_reason": "",
            "comment_summary": "",
            "highlight": "",
            "matched_tags": [],
            "distance": "600 公尺",
            "reason_score": None,
            "price_level": "$"
        }
    ]
}

response = requests.post(url, json=data)
print("狀態碼:", response.status_code)
print("回應內容:", json.dumps(response.json(), ensure_ascii=False, indent=2))