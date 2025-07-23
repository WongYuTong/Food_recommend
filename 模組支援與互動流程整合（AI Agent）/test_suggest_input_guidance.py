import requests

url = "http://localhost:8000/agent/suggest_input_guidance/"

test_cases = [
    "不想吃火鍋",
    "我吃素",
    "朋友聚餐",
    "想找便宜一點的",
    "這次想來點精緻的",
    "我不吃牛",
    "晚點想吃宵夜",
    "早午餐有推薦的嗎",
    "不知道吃什麼，不過怕辣",
    "家庭聚餐",
]

for idx, input_text in enumerate(test_cases, 1):
    response = requests.post(url, json={"text": input_text})
    print(f"\n測試 {idx}: {input_text}")
    print("狀態碼:", response.status_code)
    print("回應內容:", response.json())

