import requests

url = "http://127.0.0.1:8000/agent/generate_card_data/"
data = {
    "restaurants": [
        {
            "name": "燒肉LIKE 台北館前店",
            "rating": 4.6,
            "address": "台北市中正區館前路"
        },
        {
            "name": "甜點日記",
            "rating": 4.2,
            "address": "新北市板橋區"
        }
    ]
}

response = requests.post(url, json=data)
print("狀態碼:", response.status_code)
print("回應內容:", response.json())
