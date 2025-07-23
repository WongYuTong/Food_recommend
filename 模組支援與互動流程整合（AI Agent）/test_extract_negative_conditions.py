import requests

url = "http://localhost:8000/agent/extract_negative_conditions/"

test_sentences = [
    "我不想吃牛肉麵和甜點、義大利麵",
    "不要火鍋和燒烤",
    "不吃拉麵、壽司以及甜食",
    "別推薦牛排、還有漢堡！",
    "不想要飲料或炸雞、鹽酥雞",
    "我今天都可以，看你決定，不過不想吃麻辣鍋"
]

for i, sentence in enumerate(test_sentences, start=1):
    response = requests.post(url, json={"text": sentence})
    print(f"\n測試 {i}: {sentence}")
    print("狀態碼:", response.status_code)
    print("回應內容:", response.json())