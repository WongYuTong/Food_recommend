import requests

url = "http://localhost:8000/agent/suggest_input_guidance/"

test_cases = [
    ("我不吃辣", ["清爽", "湯品", "排除"]),
    ("我不吃牛", ["牛", "排除"]),
    ("海鮮過敏", ["海鮮", "排除"]),
    ("我吃素", ["素食", "蔬食"]),
    ("朋友聚餐", ["朋友", "聚會", "多人"]),
    ("家人吃飯", ["家庭", "多人", "寬敞"]),
    ("今天是約會", ["約會", "氣氛", "咖啡廳"]),
    ("有點商務需求", ["正式", "穩重", "高評價"]),
    ("要幫朋友慶生", ["慶生", "氣氛", "包廂"]),
    ("要帶小孩一起吃", ["小孩", "兒童", "親子"]),
    ("要請長輩吃飯", ["長輩", "家庭", "安靜"]),
    ("想找便宜的餐廳", ["便宜", "平價", "不貴"]),
    ("來點高級的", ["高級", "高端", "精緻"]),
    ("想吃宵夜", ["宵夜", "深夜"]),
    ("早午餐有推薦嗎", ["早午餐"]),
    ("有推薦的早餐嗎", ["早餐"]),
    ("想吃甜點", ["甜點"]),
    ("拉麵好嗎", ["拉麵", "日式"]),
    ("最近很想吃韓式", ["韓式"]),
    ("中式餐廳推薦", ["中式"]),
    ("義大利麵好吃嗎", ["義大利麵", "義式"]),
    ("想吃漢堡", ["漢堡", "美式"]),
    ("今天吃不多", ["輕食", "早午餐"]),
    ("我趕時間", ["快速", "外帶"]),
    ("天氣冷想吃熱的", ["湯品", "火鍋", "熱"]),
    ("今天想吃辣的", ["辣", "麻辣", "川菜"]),
    ("想吃清淡的", ["清淡", "清爽", "湯品"]),
    ("不要火鍋", ["排除"]),
    ("不想吃韓式", ["排除", "韓式"]),
    ("隨便", ["建議", "輸入"]),
]

success_count = 0
fail_count = 0
failed_cases = []

print("\n🎯 開始測試 SuggestInputGuidanceView...\n")

for idx, (text, expected_keywords) in enumerate(test_cases, 1):
    response = requests.post(url, json={"text": text})
    result = response.json().get("guidance", "")
    found = any(keyword in result for keyword in expected_keywords)

    print(f"🧪 測試 {idx:2}: {text}")
    print(f"📥 回傳內容: {result}")
    if found:
        print("✅ 匹配結果：✔️ 通過\n")
        success_count += 1
    else:
        print(f"❌ 匹配結果：❌ 失敗（應包含：{', '.join(expected_keywords)}）\n")
        fail_count += 1
        failed_cases.append((text, result, expected_keywords))

print("📊 測試結果統計")
print(f"✔️ 通過：{success_count}")
print(f"❌ 失敗：{fail_count}")

if failed_cases:
    print("\n📌 失敗案例回顧：")
    for text, response, expected in failed_cases:
        print(f"- ❌ 測試輸入：{text}")
        print(f"  回傳內容：{response}")
        print(f"  預期關鍵詞：{expected}\n")