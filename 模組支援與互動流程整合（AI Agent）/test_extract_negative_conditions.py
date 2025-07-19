import requests

url = "http://127.0.0.1:8000/agent/extract_negative_conditions/"
data = {
    "text": "我不想吃火鍋，也不要燒烤"
}

response = requests.post(url, json=data)

print("狀態碼:", response.status_code)
print("回應內容:", response.json())


