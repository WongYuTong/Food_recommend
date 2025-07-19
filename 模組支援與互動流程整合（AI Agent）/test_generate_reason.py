import requests

url = "http://localhost:8000/agent/generate_recommend_reasons/"
data = {
    "restaurants": [
        {
            "name": "這一小鍋 台北車站店",
            "rating": 4.8,
            "comments": "環境很好、氣氛佳，甜點超棒",
            "distance": 400,
            "address": "台北市中正區忠孝西路",
            "is_open": True
        },
        {
            "name": "某某燒肉店",
            "rating": 4.2,
            "comments": "服務親切，座位舒適",
            "distance": 800,
            "address": "台北市信義區",
            "is_open": False
        }
    ]
}

response = requests.post(url, json=data)
print("狀態碼:", response.status_code)
print("回應內容:", response.json())
