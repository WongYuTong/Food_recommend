import requests

url = "http://localhost:8000/agent/generate_prompt/"
data = {
    "input": "我隨便"
}

response = requests.post(url, json=data)
print("狀態碼:", response.status_code)
print("回應內容:", response.json())
