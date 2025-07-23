import requests

url = "http://localhost:8000/agent/generate_prompt/"

test_inputs = [
    "我沒特別想吃什麼",
    "都可以啦",
    "你幫我決定吧",
    "再說吧，看情況",
    "不知道吃什麼",
    "你決定",
    "還沒想好耶",
]

for i, input_text in enumerate(test_inputs, 1):
    response = requests.post(url, json={"input": input_text})
    print(f"\n測試 {i}: {input_text}")
    print("狀態碼:", response.status_code)
    print("回應內容:", response.json())


