import requests

url = "http://localhost:8000/agent/suggest_input_guidance/"
data = {
    "text": "不知道要吃什麼，但不想吃太油的"
}

response = requests.post(url, json=data)
print("狀態碼:", response.status_code)
print("回應內容:", response.json())
