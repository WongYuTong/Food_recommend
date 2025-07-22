import requests

url = "http://127.0.0.1:8000/agent/extract_negative_conditions/"
data = {
    "text": "我不想吃牛肉麵和甜點跟義大利麵，也不要火鍋、燒烤。"
}

response = requests.post(url, json=data)
print("狀態碼:", response.status_code)
print("回應內容:", response.json())
